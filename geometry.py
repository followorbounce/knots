"""Rope geometry for each knot. Content (text) lives in knots.py.

Every function returns a knot geometry dict:
  ropes   : [{'color': 'a'|'b', 'pts': [[x,y(,z)], ...]}]
  code    : over/under code (diagram knots) or None (explicit 3D z)
  objects : poles / rings the rope is tied to
  marks   : named control-point indices used by steps, {name: (rope, index)}
"""
import math
from knotlib import R, coil_y, coil_x, bump


def _rot_to_tangent(core):
    """Rotate so the curve leaves the first point heading +x; translate first point to origin."""
    a, b = core[0], core[1]
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    c, s = math.cos(-ang), math.sin(-ang)
    return [[(p[0] - a[0]) * c - (p[1] - a[1]) * s, (p[0] - a[0]) * s + (p[1] - a[1]) * c, p[2]] for p in core]


def _param_knot(f, t0, scale, zscale, ncore=72, gap=0.13, tail=3.2):
    """Open a closed parametric knot at its outer lobe. Both ends leave downwards
    and spread apart, so the tails never cross each other; then mirror x so the
    standing part is on the left."""
    core = []
    for i in range(ncore + 1):
        t = t0 + gap + (2 * math.pi - 2 * gap) * i / ncore
        x, y, z = f(t)
        core.append([x * scale, y * scale, z * zscale])
    tipx, tipy = f(t0)[0] * scale, f(t0)[1] * scale
    nx, ny = f(t0 + 1e-4)[0] * scale - tipx, f(t0 + 1e-4)[1] * scale - tipy
    ang = math.atan2(ny, nx)
    c, s = math.cos(-ang), math.sin(-ang)
    core = [[(p[0] - tipx) * c - (p[1] - tipy) * s, (p[0] - tipx) * s + (p[1] - tipy) * c, p[2]] for p in core]
    if sum(p[1] for p in core) < 0:          # body above the tails
        core = [[p[0], -p[1], -p[2]] for p in core]
    ps, pe = core[0], core[-1]
    stand = [[ps[0] + 0.55 * tail, ps[1] - 0.95 * tail, 0], [ps[0] + 0.32, ps[1] - 1.05, 0], [ps[0] + 0.06, ps[1] - 0.42, 0]]
    work = [[pe[0] + 0.02, pe[1] - 0.42, 0], [pe[0] - 0.36, pe[1] - 1.05, 0], [pe[0] - 0.55 * tail, pe[1] - 0.95 * tail, 0]]
    pts = stand + core + work
    pts = [[-p[0], p[1], p[2]] for p in pts]
    return pts, len(stand), ncore


def overhand():
    """Classic open drawing: a loop crossed over the standing part, end tucked up through it."""
    pts = [[-3.6, 0.0], [-2.2, 0.0], [-1.0, 0.0], [0.0, 0.02], [0.55, 0.27], [0.82, 0.75], [0.58, 1.22], [0.0, 1.32],
           [-0.5, 1.02], [-0.56, 0.42], [-0.4, -0.3], [-0.05, -0.62], [0.32, -0.45], [0.36, 0.12], [0.4, 0.55],
           [0.95, 0.8], [1.6, 0.78], [2.6, 0.7], [3.6, 0.66]]
    pts = _scale(pts, 1.5, 3.4)
    return {'ropes': [{'color': 'a', 'pts': pts}], 'code': 'uou', 'objects': [],
            'marks': {'start': (0, 3), 'loop': (0, 10), 'tuck': (0, 15), 'end': (0, len(pts) - 1)}}


def _fig8_path():
    return [[0.0, 4.2], [0.0, 2.8], [0.0, 1.4], [0.0, 0.3], [0.35, -0.28], [0.9, -0.36], [1.26, 0.05], [1.12, 0.56],
            [0.5, 0.78], [-0.05, 0.84], [-0.48, 1.02], [-0.78, 1.5], [-0.58, 2.0], [-0.1, 2.24], [0.4, 2.16],
            [0.76, 1.8], [0.78, 1.3], [0.64, 0.86], [0.6, 0.3], [0.62, -0.4], [0.66, -1.2], [0.7, -2.4]]


def figure_eight():
    pts = _scale(_fig8_path(), 1.45, 3.6, axis=1)
    return {'ropes': [{'color': 'a', 'pts': pts}], 'code': 'ouou', 'objects': [],
            'marks': {'start': (0, 3), 'loop': (0, 10), 'behind': (0, 15), 'through': (0, 20), 'end': (0, len(pts) - 1)}}


def _line(p0, p1, n=3):
    return [[p0[k] + (p1[k] - p0[k]) * i / n for k in range(3)] for i in range(n + 1)]


def _dedupe(pts, eps=0.02):
    out = []
    for p in pts:
        p = list(p) + [0.0] * (3 - len(p))
        if not out or math.dist(out[-1], p) > eps:
            out.append(p)
    return out


def _scale(pts, k, limit=None, axis=0):
    out = []
    for p in pts:
        q = [c * k for c in p[:2]] + list(p[2:])
        if limit is not None and abs(q[axis]) > limit:
            q[axis] = math.copysign(limit + (abs(q[axis]) - limit) * 0.45, q[axis])
        out.append(q)
    return out


def _idx_near(pts, target):
    best = min(range(len(pts)), key=lambda i: math.dist(pts[i][:2], target[:2]))
    return best


# ------------------------------------------------------------------ diagram knots

def _two_bights(code, blue_short='top', raw=False, k=1.6):
    """Two interlocked bights: yellow (left end) bends right, blue (right end) bends left.
    Short legs are the working ends. Used for the square, granny and thief knots.
    The over/under code is written for the drawing order yellow-top-first; the ropes
    are then reversed so each is drawn from its standing part, as it is tied."""
    from knotlib import ctrl_arc_positions
    red = [[-2.9, 0.19], [-2.2, 0.19], [-1.4, 0.19], [-0.85, 0.3], [-0.45, 0.72], [0.0, 0.86], [0.7, 0.86],
           [1.25, 0.66], [1.56, 0.0], [1.25, -0.66], [0.7, -0.86], [0.0, -0.86], [-0.45, -0.72], [-0.85, -0.3],
           [-1.4, -0.19], [-2.6, -0.19], [-4.6, -0.19]]
    long_, short = [[2.6, 0], [4.6, 0]], [[2.6, 0]]
    top = (short if blue_short == 'top' else long_)
    bot = (long_ if blue_short == 'top' else short)
    blue = [[x, 0.5] for x, _ in top[::-1]] + [[0.6, 0.5], [-0.6, 0.5], [-1.4, 0.5], [-1.8, 0.31], [-1.92, 0.0],
                                               [-1.8, -0.31], [-1.4, -0.5], [-0.6, -0.5], [0.6, -0.5]] + [[x, -0.5] for x, _ in bot]
    red, blue = _scale(red, k, 2.5 * k), _scale(blue, k, 2.5 * k)
    g0 = {'ropes': [{'color': 'a', 'pts': red}, {'color': 'b', 'pts': blue}], 'code': code}
    Ps = [P[::-1].copy() for P in _dense_with_z(g0)]
    nb = len(top)
    cb = ctrl_arc_positions(blue)
    fr = lambda i: 1 - cb[i] / cb[-1]
    out = {'ropes': [{'color': 'a', 'pts': Ps[0][::2].tolist() + [Ps[0][-1].tolist()]},
                     {'color': 'b', 'pts': Ps[1][::2].tolist() + [Ps[1][-1].tolist()]}],
           'code': None, 'objects': [], 'closure': [(0, 1), (1, -1)],
           'rope_fractions': {'in': (1, fr(nb + 6)), 'bend': (1, fr(nb + 2))},
           'marks': {'red': (0, len(Ps[0][::2])), 'blue': (1, len(Ps[1][::2]))}}
    if raw:
        out['dense'] = Ps
    return out


def square_knot():
    return _two_bights('uouuou')


def granny_knot():
    return _two_bights('ououou')


def thief_knot():
    return _two_bights('uouuou', blue_short='bottom')


def sheet_bend():
    """Red forms the bight (bend on the right). Blue comes up through it, round
    the back of both legs, and is tucked under itself."""
    red = [[-4.6, -0.34], [-2.5, -0.34], [-0.5, -0.34], [0.6, -0.34], [1.05, -0.24], [1.24, 0.0], [1.05, 0.24],
           [0.6, 0.34], [-0.5, 0.34], [-1.6, 0.34], [-2.5, 0.34]]
    blue = [[-0.02, -4.4], [-0.02, -2.2], [-0.02, -0.9], [0.0, -0.3], [0.0, 0.3], [-0.08, 0.72], [-0.38, 0.95],
            [-0.78, 0.8], [-0.92, 0.34], [-0.92, -0.34], [-0.8, -0.8], [-0.5, -0.92], [-0.42, -0.55], [-0.45, -0.25],
            [-0.3, -0.06], [0.2, 0.02], [0.6, 0.04]]
    red, blue = _scale(red, 1.6, 4.0), _scale(blue, 1.6, 4.0, axis=1)
    return {'ropes': [{'color': 'a', 'pts': red}, {'color': 'b', 'pts': blue}], 'code': 'ououoo', 'objects': [],
            'marks': {'red': (0, len(red) - 1), 'b_up': (1, 5), 'b_round': (1, 11), 'b_tuck': (1, len(blue) - 1)}}


def bowline():
    pts = [[0.0, 4.4], [0.0, 3.0], [0.0, 1.6], [0.0, 0.55], [0.3, 0.12], [0.8, 0.08], [1.12, 0.55], [1.02, 1.05],
           [0.62, 1.32], [0.15, 1.26], [-0.3, 1.02], [-0.55, 0.42], [-0.72, -0.8], [-0.62, -2.3], [0.2, -3.0],
           [1.0, -2.3], [1.1, -1.0], [0.9, -0.3], [0.76, 0.3], [0.72, 0.9], [0.66, 1.62], [0.32, 2.12], [-0.12, 2.22],
           [-0.4, 2.0], [-0.3, 1.72], [0.18, 1.52], [0.38, 1.12], [0.4, 0.55], [0.44, -0.2], [0.55, -1.25]]
    pts = _scale(pts, 1.6, 4.4, axis=1)
    return {'ropes': [{'color': 'a', 'pts': pts}], 'code': 'ouuoouu', 'objects': [],
            'marks': {'stand': (0, 3), 'loop': (0, 11), 'eye': (0, 17), 'up': (0, 20), 'round': (0, 24), 'down': (0, len(pts) - 1)}}


# ------------------------------------------------------------------ 3D knots on objects

POLE = 0.45
WRAP = POLE + R + 0.015          # rope centre distance from pole axis


def _clove_core(cx, cz, rho, lift, variant='clove'):
    """Clove hitch / constrictor round a vertical axis at (cx, cz).
    The standing part arrives tangentially at the front heading +x at height ys;
    the end leaves tangentially at the front heading +x at height ye.
    Returns (points, ys, ye, index where the rider starts, index where the tuck starts)."""
    cl = variant == 'clove'
    ys, ye = (0.17, -0.17) if cl else (-0.15, 0.15)
    hi, lo = 0.58, -0.58
    pts = coil_y(cx, cz, rho, 0, 1.5 * math.pi, ys, hi)[1:]                     # round the back
    i_rider = len(pts)
    amt = lift * (1.3 if cl else 2.5)
    k = math.tanh(math.pi / 2 / 0.32)
    pts += coil_y(cx, cz, rho, 1.5 * math.pi, 2.5 * math.pi, hi, lo, n=28,
                  rho_fn=lambda a, t: rho + bump(a, 2 * math.pi, 1.1, amt),
                  yfn=lambda a, t: -hi * math.tanh((a - 2 * math.pi) / 0.32) / k)[1:]   # rider across the front
    pts += coil_y(cx, cz, rho, 2.5 * math.pi, 3.5 * math.pi, lo, lo)[1:]           # round the back again
    i_tuck = len(pts)
    if cl:
        pts += coil_y(cx, cz, rho, 3.5 * math.pi, 4 * math.pi, lo, ye, ease=0.6)[1:]
    else:   # the end rises late and crosses over the standing part, still under the rider
        pts += coil_y(cx, cz, rho, 3.5 * math.pi, 4 * math.pi, lo, ye, ease=2.6,
                      rho_fn=lambda a, t: rho + bump(a, 4 * math.pi - 0.3, 1.1, lift * 1.3))[1:]
    return pts, ys, ye, i_rider, i_tuck


def clove_hitch(variant='clove'):
    rho, lift = WRAP, 2.3 * R
    core, ys, ye, i_r, i_t = _clove_core(0.0, 0.0, rho, lift, variant)
    stand = [[-2.9, ys, rho], [-1.8, ys, rho], [-0.9, ys, rho], [0.0, ys, rho]]
    end = [[0.8, ye, rho], [1.8, ye, rho], [2.9, ye, rho]]
    pts = _dedupe(stand + core + end)
    k0 = 3
    return {'ropes': [{'color': 'c' if variant == 'clove' else 'b', 'pts': pts}], 'code': None,
            'objects': [{'type': 'pole', 'axis': 'y', 'c': [0, 0, 0], 'radius': POLE, 'len': 3.6}],
            'marks': {'stand': (0, k0), 'behind': (0, k0 + i_r), 'rider': (0, k0 + i_t),
                      'end': (0, len(pts) - 1)}}


def constrictor():
    return clove_hitch('constrictor')


def _tanh_y(mid, amp, centre, w=0.32):
    k = math.tanh(math.pi / 2 / w)
    return lambda a, t: mid - amp * math.tanh((a - centre) / w) / k


def rolling_hitch():
    """Built round a vertical pole (standing part from the left), then turned so the
    pole is horizontal and the standing part hangs down."""
    rho, lift = WRAP, 2.3 * R
    P = math.pi
    ys, ye = 0.1, -0.66
    pts = [[-2.9, ys, rho], [-1.8, ys, rho], [-0.9, ys, rho], [0.0, ys, rho]]
    k0 = len(pts) - 1
    pts += coil_y(0, 0, rho, 0, 1.5 * P, ys, 0.95)[1:]
    pts += coil_y(0, 0, rho, 1.5 * P, 2.5 * P, 0, 0, n=28, rho_fn=lambda a, t: rho + bump(a, 2 * P, 1.1, lift * 1.3),
                  yfn=_tanh_y(0.35, 0.6, 2 * P))[1:]
    i1 = len(pts) - 1
    pts += coil_y(0, 0, rho, 2.5 * P, 3.5 * P, -0.25, 0.4)[1:]
    pts += coil_y(0, 0, rho, 3.5 * P, 4.5 * P, 0, 0, n=28, rho_fn=lambda a, t: rho + bump(a, 4 * P, 1.1, lift * 1.3),
                  yfn=_tanh_y(-0.3, 0.7, 4 * P))[1:]
    i2 = len(pts) - 1
    pts += coil_y(0, 0, rho, 4.5 * P, 5.5 * P, -1.0, -1.2)[1:]
    pts += coil_y(0, 0, rho, 5.5 * P, 6 * P, -1.2, ye, ease=0.6)[1:]
    pts += [[0.8, ye, rho], [1.8, ye, rho], [2.9, ye, rho]]
    pts = _dedupe(pts)
    pts = [[-p[1], p[0], p[2]] for p in pts]          # pole horizontal, standing part hangs down
    return {'ropes': [{'color': 'c', 'pts': pts}], 'code': None,
            'objects': [{'type': 'pole', 'axis': 'x', 'c': [0, 0, 0], 'radius': POLE, 'len': 4.0}],
            'marks': {'stand': (0, k0), 'r1': (0, i1), 'r2': (0, i2), 'end': (0, len(pts) - 1)}}


RING_C, RING_R, RING_T = (0.0, 1.55), 0.85, 0.09


def _ring_y(x):
    return RING_C[1] - math.sqrt(RING_R ** 2 - x ** 2)


def round_turn_two_half_hitches():
    rho = RING_T + R + 0.02
    xs = -0.32
    pts = [[xs, -3.4, rho], [xs, -2.0, rho], [xs, -0.9, rho], [xs, _ring_y(xs) - 0.5, rho]]
    k0 = len(pts)
    # round turn: 1.5 laps round the bottom of the ring, moving right
    n = 34
    for k in range(n + 1):
        t = k / n
        a = 3 * math.pi * t
        x = xs + 0.62 * t
        pts.append([x, _ring_y(x) + rho * math.sin(a), rho * math.cos(a)])
    i_rt = len(pts) - 1
    xe = xs + 0.62
    # end drops down behind, swings right and comes to the front of the standing part
    cx, cz = xs, rho                       # half hitches are tied round the standing part
    rho2 = 2 * R + 0.03
    yc = -1.25
    pts += [[xe + 0.05, 0.05, -0.2], [xe + 0.4, -0.45, 0.1], [cx + 1.05, yc + 0.17, cz + rho2], [cx + 0.5, yc + 0.17, cz + rho2]]
    i_down = len(pts) - 1
    core, ys, ye, i_r, i_t = _clove_core(0.0, 0.0, rho2, 2.3 * R, 'clove')
    # mirror the clove (approach from the right) and move it onto the standing part
    core = [[cx - p[0], yc + p[1], cz + p[2]] for p in core]
    pts += [[cx, yc + ys, cz + rho2]]
    s0 = len(pts)
    pts += core
    i_hh1 = s0 + i_r + 26
    pts += [[cx - 0.5, yc + ye, cz + rho2], [cx - 0.95, yc - 0.3, cz + rho2 * 0.7], [cx - 1.1, yc - 1.2, 0.3], [cx - 1.15, yc - 2.0, 0.3]]
    pts = _dedupe(pts)
    return {'ropes': [{'color': 'a', 'pts': pts}], 'code': None,
            'objects': [{'type': 'ring', 'c': [RING_C[0], RING_C[1], 0], 'radius': RING_R, 'tube': RING_T}],
            'marks': {'stand': (0, k0), 'turn': (0, i_rt), 'down': (0, i_down), 'hh1': (0, i_hh1), 'end': (0, len(pts) - 1)}}


def double_fishermans():
    """Each rope ties a double overhand round the other. Rope B is rope A turned
    half a turn about the viewing axis, so the two halves nest."""
    off = 2 * R + 0.02
    rho = off + 2 * R + 0.04
    A = [[-3.6, 0, 0], [-2.4, 0, 0], [-1.2, 0, 0], [-0.55, 0, 0], [0.55, -off, 0], [1.4, -off, 0], [1.95, -off, 0]]
    k0 = len(A) - 1
    A += [[2.25, -off - 0.12, 0.12], [2.3, -rho + 0.02, 0.25]]
    x1, x0 = 2.05, 0.85
    n = 40
    for k in range(n + 1):                               # two turns, working back towards the middle
        t = k / n
        a = 1.5 * math.pi + 4 * math.pi * t
        A.append([x1 + (x0 - x1) * t, rho * math.sin(a), rho * math.cos(a)])
    i_coil = len(A) - 1
    for k in range(1, 7):                                # half turn more, then into the middle
        a = 5.5 * math.pi + 0.5 * math.pi * k / 6
        A.append([x0 - 0.12 * k / 6, rho * math.sin(a), rho * math.cos(a)])
    A += [[0.62, off + 0.08, 0.14], [0.85, off, 0], [1.5, off, 0], [2.4, off, 0], [3.2, off, 0]]
    A = _dedupe(A)
    B = [[-p[0], -p[1], p[2]] for p in A]
    return {'ropes': [{'color': 'a', 'pts': A}, {'color': 'b', 'pts': B}], 'code': None, 'objects': [],
            'marks': {'a_lay': (0, k0), 'a_coil': (0, i_coil), 'a_tuck': (0, len(A) - 1),
                      'b_lay': (1, k0), 'b_coil': (1, i_coil), 'b_tuck': (1, len(B) - 1)}}


def prusik():
    """A loop of cord round a vertical main rope: three turns above and three below
    the legs, joined by the bight, which lies across the legs."""
    rho = 2 * R + 0.03
    main = [[0, -3.0, 0], [0, -1.5, 0], [0, 0, 0], [0, 1.5, 0], [0, 3.0, 0]]
    yl = R + 0.03
    turns, pitch = 3, 2 * R + 0.05
    far = 3.0
    sling = [[far, yl, 0], [far - 1.2, yl, 0], [1.0, yl, 0], [rho + 0.12, yl, 0]]
    k0 = len(sling) - 1
    up = coil_y(0, 0, rho, 0.5 * math.pi, 0.5 * math.pi + 2 * math.pi * turns, yl + 0.05, yl + 0.05 + pitch * turns, n=60)
    sling += up[1:]
    i_up = len(sling) - 1
    top, bot = up[-1][1], -up[-1][1]
    zb = 2 * R + 0.06
    zb = 2 * R + 0.05
    sling += [[rho + 0.25, top - 0.04, 0.1], [rho + 0.3, top - 0.42, zb], [rho + 0.3, 0.0, zb],
              [rho + 0.3, bot + 0.42, zb], [rho + 0.25, bot + 0.04, 0.1]]
    i_bridge = len(sling) - 1
    down = coil_y(0, 0, rho, 0.5 * math.pi + 2 * math.pi * turns, 0.5 * math.pi, bot, -(yl + 0.05), n=60)
    sling += down + [[rho + 0.12, -yl, 0], [1.0, -yl, 0], [far - 1.2, -yl, 0], [far, -yl, 0],
                     [far + 0.3, -yl * 0.3, 0], [far + 0.3, yl * 0.3, 0], [far, yl + 0.002, 0]]
    sling = _dedupe(sling)
    return {'ropes': [{'color': 'b', 'pts': main}, {'color': 'a', 'pts': sling, 'closed': True}], 'code': None, 'objects': [],
            'marks': {'main': (0, len(main) - 1), 'legs': (1, k0), 'up': (1, i_up), 'bridge': (1, i_bridge),
                      'all': (1, len(sling) - 1)}}


def figure_eight_loop():
    """A figure-eight tied in a doubled rope: both strands follow the same path,
    and the far end of the doubled part becomes the eye."""
    import numpy as np
    from knotlib import catmull_rom, resample, z_profile, find_crossings
    path = _scale(_fig8_path()[:-1] + [[0.68, -1.9]], 2.1, 4.6, axis=1)
    dense = catmull_rom(path, per_seg=10)
    P, _ = resample(dense, 0.05)
    # heights from the over/under code of the single-strand figure-eight
    from knotlib import apply_code
    P = apply_code([P], 'ouou')[0]
    T = np.gradient(P[:, :2], axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    N = np.column_stack([-T[:, 1], T[:, 0]])
    d = R + 0.025
    A = np.column_stack([P[:, :2] + d * N, P[:, 2] * 1.35])
    B = np.column_stack([P[:, :2] - d * N, P[:, 2] * 1.35])
    end, tang, nrm = P[-1, :2], T[-1], N[-1]
    eye = []
    for k in range(1, 26):
        a = math.pi * k / 26
        c = end + tang * (0.2 + 1.9 * math.sin(a) ** 0.8) + nrm * ((d + 0.95) * math.cos(a))
        eye.append([float(c[0]), float(c[1]), 0.0])
    half = len(eye) // 2
    s1 = _dedupe(A[::3].tolist() + eye[:half + 1])
    s2 = _dedupe(B[::3].tolist() + eye[half:][::-1])
    # step fractions along a strand, from the single-strand control points
    from knotlib import ctrl_arc_positions
    cs = ctrl_arc_positions(path)
    base_len = cs[-1]
    tot = base_len + 2.2
    fr = {k: cs[i] / tot for k, i in (('start', 3), ('loop', 10), ('behind', 15), ('through', 20))}
    return {'ropes': [{'color': 'c', 'pts': s1}, {'color': 'c', 'pts': s2}], 'code': None, 'objects': [], 'joined': True,
            'fractions': fr, 'marks': {'s1': (0, len(s1) - 1), 's2': (1, len(s2) - 1)}}


# ------------------------------------------------------------------ wave 2 helpers

def _coil_knot(n, standing_len=3.4, tail_len=2.6, gap=None):
    """Multiple overhand: the end comes back and wraps n times round its own
    standing part, then tucks back through the wraps and leaves past the U-turn.
    n=1 is the plain overhand, n=2 the double overhand, and so on."""
    off = R + 0.03
    rho = off + 2 * R + 0.06
    pitch = gap or (2 * R + 0.07)
    x1 = 0.55 * n
    x0 = x1 - pitch * n - 0.1
    pts = [[-standing_len, -off, 0], [x0 - 1.2, -off, 0], [x0 - 0.2, -off, 0], [x1 + 0.35, -off, 0]]
    k_stand = 2
    pts += [[x1 + 0.7, -off - 0.1, 0.12], [x1 + 0.75, -rho + 0.05, 0.3]]
    k_turn = len(pts) - 1
    m = 14 * n
    for k in range(m + 1):
        t = k / m
        a = 1.5 * math.pi + 2 * math.pi * n * t
        pts.append([x1 + (x0 - x1) * t, rho * math.sin(a), rho * math.cos(a)])
    k_coil = len(pts) - 1
    for k in range(1, 7):
        a = 1.5 * math.pi + 2 * math.pi * n + 0.5 * math.pi * k / 6
        pts.append([x0 - 0.1 * k / 6, rho * math.sin(a), rho * math.cos(a)])
    pts += [[x0 - 0.2, off + 0.08, 0.12], [x0 + 0.05, off, 0], [x1 + 0.3, off, 0], [x1 + 0.3 + tail_len, off, 0]]
    pts = _dedupe(pts)
    return pts, {'stand': (0, k_stand), 'turn': (0, k_turn), 'coil': (0, k_coil), 'end': (0, len(pts) - 1)}


def _single(pts, marks, color='a', **kw):
    d = {'ropes': [{'color': color, 'pts': pts}], 'code': None, 'objects': [], 'marks': marks, 'closure': [(0, 1)]}
    d.update(kw)
    return d


def double_overhand():
    pts, m = _coil_knot(2)
    return _single(pts, m, 'b')


def multiple_overhand():
    pts, m = _coil_knot(4)
    return _single(pts, m, 'b')


def _dense_with_z(knot_geo, rope=0):
    """Sample a geometry's rope and resolve its heights (code or explicit z)."""
    import numpy as np
    from knotlib import catmull_rom, resample, apply_code
    Ps = [resample(catmull_rom(r['pts']))[0] for r in knot_geo['ropes']]
    if knot_geo.get('code'):
        Ps = apply_code(Ps, knot_geo['code'])
    return Ps


def _ctrl_sample(g, P, i, rope=0):
    from knotlib import ctrl_arc_positions
    cs = ctrl_arc_positions(g['ropes'][rope]['pts'])
    return int(round(cs[i] / cs[-1] * (len(P) - 1)))


def _slip(P, s0, length=None, eye=0.75, from_start=False, ramp=14, tail=0.9, tail_turn=1.0, tail_z=0.0, side=1):
    """Turn the end of path P (dense, with z) after sample s0 into a bight: the rope
    follows P to its end doubled, turns round in a small eye, and comes back out
    beside itself as a short tail. Returns control points (every 2nd sample)."""
    import numpy as np
    if from_start:
        P = P[::-1].copy()
        s0 = len(P) - 1 - s0
    T = np.gradient(P[:, :2], axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    N = np.column_stack([-T[:, 1], T[:, 0]]) * side
    d = R + 0.03
    end = len(P) - 1 if length is None else min(len(P) - 1, s0 + length)
    idx = np.arange(len(P))
    wA = np.clip((idx - (s0 - ramp)) / ramp, 0, 1)
    A = np.column_stack([P[:, :2] + (d * wA)[:, None] * N, P[:, 2]])
    head = A[:end + 1]
    tip, tang, nrm = P[end, :2], T[end], N[end]
    loop = []
    for k in range(1, 22):
        a = math.pi * k / 22
        c = tip + tang * (eye * math.sin(a) ** 0.7) + nrm * math.cos(a) * (d + 0.42 * eye * math.sin(a))
        loop.append([float(c[0]), float(c[1]), float(P[end, 2])])
    # return strand: offset -d back to s0, then the short tail leaves away from the knot
    back = []
    for i in range(end, s0 - 1, -1):
        back.append([float(P[i, 0] - d * N[i, 0]), float(P[i, 1] - d * N[i, 1]), float(P[i, 2])])
    t0 = -T[s0]
    out = t0 * math.cos(tail_turn) + (-N[s0]) * math.sin(tail_turn)
    base = np.array(back[-1][:2])
    for k in range(1, 5):
        q = base + out * (tail * k / 4) - N[s0] * 0.12 * k / 4
        back.append([float(q[0]), float(q[1]), float(P[s0, 2]) + (tail_z - float(P[s0, 2])) * min(1, k / 2)])
    pts = head[::2].tolist() + loop + back[::2]
    if from_start:
        pts = pts[::-1]
    return _dedupe(pts)


def slipped_overhand():
    g = overhand()
    wide = [[-3.6, 0.0], [-2.2, 0.0], [-1.0, 0.0], [0.0, 0.02], [0.75, 0.27], [1.08, 0.78], [0.72, 1.3], [0.0, 1.38],
            [-0.5, 1.05], [-0.56, 0.42], [-0.4, -0.3], [-0.05, -0.62], [0.3, -0.45], [0.32, 0.12], [0.36, 0.6],
            [1.2, 0.95], [1.8, 0.95], [2.6, 0.9], [3.6, 0.86]]
    g['ropes'][0]['pts'] = _scale(wide, 1.5, 3.4)
    P = _dense_with_z(g)[0]
    s0, s1 = _ctrl_sample(g, P, 10), _ctrl_sample(g, P, 16)
    pts = _slip(P, s0, length=s1 - s0, eye=1.3, tail_turn=1.2)
    n = len(pts)
    return {'ropes': [{'color': 'a', 'pts': pts}], 'code': None, 'objects': [], 'closure': [(0, 1)],
            'fractions': {'start': 0.2, 'loop': 0.45, 'tuck': 0.62}, 'marks': {'end': (0, n - 1)}}


def slipped_figure_eight():
    g = figure_eight()
    P = _dense_with_z(g)[0]
    s0, s1 = _ctrl_sample(g, P, 16), _ctrl_sample(g, P, 20)
    pts = _slip(P, s0, length=s1 - s0, eye=1.0, tail_turn=0.6, tail=0.9)
    n = len(pts)
    return {'ropes': [{'color': 'a', 'pts': pts}], 'code': None, 'objects': [], 'closure': [(0, 1)],
            'fractions': {'start': 0.12, 'loop': 0.4, 'behind': 0.53, 'through': 0.71}, 'marks': {'end': (0, n - 1)}}


def stevedore():
    """Figure-eight with one more turn round the standing part before the tuck."""
    p = [[0.0, 5.0], [0.0, 3.9], [0.0, 2.6], [0.0, 1.4], [0.0, 0.3], [0.35, -0.28], [0.9, -0.36], [1.26, 0.05],
         [1.12, 0.56], [0.5, 0.78], [-0.05, 0.84], [-0.48, 1.02], [-0.78, 1.5], [-0.58, 2.0], [-0.1, 2.24],
         [0.4, 2.3], [0.62, 2.55], [0.3, 2.74], [-0.2, 2.82], [-0.55, 3.0], [-0.5, 3.32], [-0.05, 3.42], [0.45, 3.4],
         [0.88, 3.05], [0.98, 2.3], [0.86, 1.4], [0.64, 0.86], [0.6, 0.3], [0.62, -0.4], [0.66, -1.2], [0.7, -2.2]]
    p = _scale(p, 1.4, 5.2, axis=1)
    return {'ropes': [{'color': 'c', 'pts': p}], 'code': 'ououou', 'objects': [], 'closure': [(0, 1)],
            'marks': {'start': (0, 4), 'loop': (0, 11), 'behind': (0, 16), 'again': (0, 23), 'through': (0, 28),
                      'end': (0, len(p) - 1)}}


SLIP_K = 2.2


def slipped_square_knot():
    """Square knot with the blue working end pulled through as a bight."""
    g = _two_bights('uouuou', raw=True, k=SLIP_K)
    Ps = g['dense']
    n1 = len(Ps[1])
    s0 = int(round(g['rope_fractions']['bend'][1] * (n1 - 1))) + 30
    blue = _slip(Ps[1], s0, eye=1.6, tail=0.7, tail_turn=-1.2)
    red = Ps[0][::2].tolist() + [Ps[0][-1].tolist()]
    return {'ropes': [{'color': 'a', 'pts': red}, {'color': 'b', 'pts': blue}], 'code': None, 'objects': [],
            'rope_fractions': {'in': (1, 0.28), 'bend': (1, 0.4)}, 'marks': {'red': (0, len(red) - 1), 'blue': (1, len(blue) - 1)}}


def bow_knot():
    """Shoelace bow: a square knot with both working ends pulled through as bights."""
    g = _two_bights('uouuou', raw=True, k=SLIP_K)
    Ps = g['dense']
    n0, n1 = len(Ps[0]), len(Ps[1])
    s_b = int(round(g['rope_fractions']['bend'][1] * (n1 - 1))) + 30
    s_r = int(round(0.66 * (n0 - 1)))
    blue = _slip(Ps[1], s_b, eye=1.6, tail=0.7, tail_turn=-1.2)
    red = _slip(Ps[0], s_r, eye=1.8, tail=0.7, tail_turn=1.2)
    return {'ropes': [{'color': 'a', 'pts': red}, {'color': 'b', 'pts': blue}], 'code': None, 'objects': [],
            'rope_fractions': {'in': (1, 0.28), 'bend': (1, 0.4)}, 'marks': {'red': (0, len(red) - 1), 'blue': (1, len(blue) - 1)}}


def _doubled(path, code, eye_len=1.9, eye_w=0.95, z_gain=1.35, closure_code=None):
    """Tie a knot in a doubled rope: both strands follow `path` (2D control points
    with an over/under code), and the far end becomes an eye.
    Returns (strand A, eye points, strand B) as dense numpy arrays / lists."""
    import numpy as np
    from knotlib import catmull_rom, resample, apply_code
    P, _ = resample(catmull_rom(path, per_seg=10), 0.05)
    P = apply_code([P], code)[0]
    T = np.gradient(P[:, :2], axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    N = np.column_stack([-T[:, 1], T[:, 0]])
    d = R + 0.025
    A = np.column_stack([P[:, :2] + d * N, P[:, 2] * z_gain])
    B = np.column_stack([P[:, :2] - d * N, P[:, 2] * z_gain])
    end, tang, nrm = P[-1, :2], T[-1], N[-1]
    eye = []
    for k in range(1, 26):
        a = math.pi * k / 26
        c = end + tang * (0.2 + eye_len * math.sin(a) ** 0.8) + nrm * ((d + eye_w) * math.cos(a))
        eye.append([float(c[0]), float(c[1]), 0.0])
    return A, eye, B


def _rot(pts, kind):
    if kind == 'cw':        # (x, y) -> (y, -x)
        return [[p[1], -p[0]] + list(p[2:]) for p in pts]
    if kind == 'ccw':
        return [[-p[1], p[0]] + list(p[2:]) for p in pts]
    return pts


def overhand_loop():
    """Overhand knot tied in a doubled rope; standing part up, eye down."""
    base = [[-3.6, 0.0], [-2.2, 0.0], [-1.0, 0.0], [0.0, 0.02], [0.55, 0.27], [0.82, 0.75], [0.58, 1.22], [0.0, 1.32],
            [-0.5, 1.02], [-0.56, 0.42], [-0.4, -0.3], [-0.05, -0.62], [0.32, -0.45], [0.36, 0.12], [0.4, 0.55],
            [0.95, 0.8], [1.6, 0.78]]
    base = _rot(_scale(base, 2.3, 4.0), 'cw')
    A, eye, B = _doubled(base, 'uou', eye_len=2.4, eye_w=1.1)
    s1 = _dedupe(A[::3].tolist() + eye[:13])
    s2 = _dedupe(B[::3].tolist() + eye[12:][::-1])
    from knotlib import ctrl_arc_positions
    cs = ctrl_arc_positions(base)
    tot = cs[-1] + 2.0
    fr = {k: cs[i] / tot for k, i in (('start', 3), ('loop', 10), ('tuck', 15))}
    return {'ropes': [{'color': 'b', 'pts': s1}, {'color': 'b', 'pts': s2}], 'code': None, 'objects': [], 'joined': True,
            'fractions': fr, 'marks': {'s1': (0, len(s1) - 1), 's2': (1, len(s2) - 1)}}


def threaded_figure_eight_loop():
    """Figure-eight follow-through: a single figure-eight, the end taken round
    (through a harness, say) and traced back alongside every part of the knot."""
    path = _scale(_fig8_path()[:-1] + [[0.68, -1.9]], 2.1, 4.6, axis=1)
    A, eye, B = _doubled(path, 'ouou')
    a_pts = A[::3].tolist()
    pts = _dedupe(a_pts + eye + B[::-3].tolist())
    from knotlib import ctrl_arc_positions
    cs = ctrl_arc_positions(path)
    la = cs[-1]
    tot = la * 2 + 3.6
    return {'ropes': [{'color': 'c', 'pts': pts}], 'code': None, 'objects': [],
            'fractions': {'single': (la * 0.97) / tot, 'round': (la + 3.4) / tot, 'half': (la + 3.4 + la * 0.45) / tot},
            'marks': {'end': (0, len(pts) - 1)}}


def _fisher_half(n, off, rho, x0=0.85, pitch=None):
    """Right-hand half of a fisherman's-type knot: rope A arrives from the left at
    y=-off, turns, wraps n times round the core (y=0) and itself, tucks back
    through the wraps and leaves to the right at y=+off. Returns points from the
    arrival point on."""
    pitch = pitch or (2 * R + 0.07)
    x1 = x0 + pitch * n + 0.35
    pts = [[x0 - 0.3, -off, 0], [x1 - 0.1, -off, 0], [x1 + 0.2, -off - 0.12, 0.12], [x1 + 0.25, -rho + 0.02, 0.25]]
    m = 20 * n
    for k in range(m + 1):
        t = k / m
        a = 1.5 * math.pi + 2 * math.pi * n * t
        pts.append([x1 + (x0 - x1) * t, rho * math.sin(a), rho * math.cos(a)])
    i_coil = len(pts) - 1
    for k in range(1, 7):
        a = 1.5 * math.pi + 2 * math.pi * n + 0.5 * math.pi * k / 6
        pts.append([x0 - 0.12 * k / 6, rho * math.sin(a), rho * math.cos(a)])
    pts += [[x0 - 0.23, off + 0.08, 0.14], [x0, off, 0], [x1 + 0.4, off, 0], [x1 + 1.3, off, 0], [x1 + 2.2, off, 0]]
    return pts, i_coil


def _fisher_loop(n, color):
    """Englishman's (fisherman's) loop: the end and the standing part each tie an
    overhand (or double overhand) round the other, and the two knots jam together."""
    off = 2 * R + 0.02
    rho = off + 2 * R + 0.04
    half, i_coil = _fisher_half(n, off, rho)
    B_knot = [[-p[0], -p[1], p[2]] for p in half]
    stand = [[4.2, 0, 0], [3.0, 0, 0], [1.6, 0, 0], [0.6, 0, 0], [-0.6, off, 0]]
    bx = B_knot[-1][0]
    eye = [[bx - 0.6, -off + 0.05, 0], [bx - 0.95, 0.35, 0], [bx - 0.7, 1.3, 0], [bx + 0.3, 1.7, 0],
           [bx + 1.15, 1.05, 0], [bx + 1.4, 0.3, 0], [bx + 1.7, 0.0, 0], [-0.55, 0.0, 0]]
    pts = _dedupe(stand + B_knot[1:] + eye + half)
    k1 = len(stand) + len(B_knot) - 2
    return {'ropes': [{'color': color, 'pts': pts}], 'code': None, 'objects': [],
            'marks': {'stand': (0, len(stand) - 1), 'first': (0, k1), 'eye': (0, k1 + len(eye)), 'end': (0, len(pts) - 1)}}


def englishmans_loop():
    return _fisher_loop(1, 'a')


def double_englishmans_loop():
    return _fisher_loop(2, 'b')


def double_overhand_noose():
    """Strangle noose: the end ties a double overhand round its own standing part,
    so the loop slides closed under load."""
    off = 2 * R + 0.02
    rho = off + 2 * R + 0.04
    half, i_coil = _fisher_half(2, off, rho, x0=0.85)
    stand = [[4.4, 0, 0], [3.2, 0, 0], [2.0, 0, 0], [0.8, 0, 0], [-0.2, 0, 0]]
    eye = [[-1.3, 0.4, 0], [-2.6, 1.1, 0], [-3.6, 0.6, 0], [-3.8, -0.5, 0], [-2.9, -1.2, 0], [-1.7, -0.8, 0],
           [-0.9, -off, 0]]
    pts = _dedupe(stand + eye + half)
    k1 = len(stand) + len(eye)
    return {'ropes': [{'color': 'a', 'pts': pts}], 'code': None, 'objects': [],
            'marks': {'loop': (0, k1), 'coil': (0, k1 + i_coil), 'end': (0, len(pts) - 1)}}


def cow_hitch():
    """Lark's head on a rail: one turn each side of the legs, joined by the bight,
    which lies across the legs. Built round a vertical axis, then turned so the
    rail is horizontal and both legs hang down."""
    rho = POLE + R + 0.015
    yl = R + 0.04
    pitch = 2 * R + 0.06
    legs_x = 3.2
    up = coil_y(0, 0, rho, 0.5 * math.pi, 2.5 * math.pi, yl + 0.05, yl + 0.05 + pitch, n=30)
    top = up[-1][1]
    zb = rho + 2 * R + 0.05
    bridge = [[rho + 0.18, top + 0.02, 0.18], [rho + 0.3, top * 0.55, 0.42], [rho + 0.32, 0.0, 0.46],
              [rho + 0.3, -top * 0.55, 0.42], [rho + 0.18, -top - 0.02, 0.18]]
    down = coil_y(0, 0, rho, 2.5 * math.pi, 0.5 * math.pi, -top, -(yl + 0.05), n=30)
    leg1 = [[legs_x, yl, 0], [legs_x - 1.2, yl, 0], [rho + 0.6, yl, 0], [rho + 0.15, yl + 0.02, 0]]
    leg2 = [[rho + 0.15, -yl - 0.02, 0], [rho + 0.6, -yl, 0], [legs_x - 1.2, -yl, 0], [legs_x, -yl, 0]]
    pts = _dedupe(leg1 + up[1:] + bridge + down + leg2)
    pts = [[p[1], -p[0], p[2]] for p in pts]
    k_up = len(leg1) + len(up) - 2
    return {'ropes': [{'color': 'a', 'pts': pts}], 'code': None,
            'objects': [{'type': 'pole', 'axis': 'x', 'c': [0, 0, 0], 'radius': POLE, 'len': 3.6}],
            'marks': {'leg': (0, len(leg1) - 1), 'over': (0, k_up), 'bridge': (0, k_up + len(bridge)), 'end': (0, len(pts) - 1)}}


def round_turn_bowline():
    """Bowline with the small loop taken twice round (two turns), for more grip."""
    p = [[0.0, 4.6], [0.0, 3.4], [0.0, 2.2], [0.0, 1.0], [0.0, 0.55], [0.3, 0.12], [0.8, 0.08], [1.12, 0.55],
         [1.02, 1.05], [0.62, 1.32], [0.15, 1.26], [-0.3, 1.02], [-0.5, 0.4], [-0.15, -0.25], [0.8, -0.32],
         [1.45, 0.4], [1.35, 1.25], [0.7, 1.64], [0.1, 1.56], [-0.4, 1.28], [-0.85, 0.4], [-0.95, -1.0],
         [-0.7, -2.4], [0.2, -3.1], [1.1, -2.4], [1.22, -1.0], [0.98, -0.5], [0.84, 0.2], [0.76, 0.75],
         [0.72, 1.3], [0.7, 1.68], [0.66, 2.2], [0.32, 2.62], [-0.12, 2.66], [-0.42, 2.4], [-0.3, 2.05],
         [0.18, 1.9], [0.38, 1.55], [0.4, 1.0], [0.42, 0.2], [0.45, -0.45], [0.5, -1.4]]
    p = _scale(p, 1.6, 4.6, axis=1)
    return {'ropes': [{'color': 'b', 'pts': p}], 'code': 'ouuuoouuoouu', 'objects': [],
            'marks': {'stand': (0, 4), 'loop1': (0, 11), 'loop2': (0, 19), 'eye': (0, 26), 'up': (0, 31),
                      'round': (0, 35), 'down': (0, len(p) - 1)}}
