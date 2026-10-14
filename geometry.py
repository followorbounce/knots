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


def _ring_hitch(laps=1.5, toward_ring=False, yc=-1.25, single=False):
    """A turn (or round turn) on the bottom of a ring, then a clove hitch round the
    standing part. toward_ring=True builds the clove upward, toward the ring
    (buntline hitch); otherwise downward, away from it (two half hitches)."""
    rho = RING_T + R + 0.02
    xs = -0.32
    pts = [[xs, -3.4, rho], [xs, -2.0, rho], [xs, -0.9, rho], [xs, _ring_y(xs) - 0.5, rho]]
    k0 = len(pts)
    shift = 0.62 * laps / 1.5
    n = int(23 * laps)
    for k in range(n + 1):
        t = k / n
        a = 2 * math.pi * laps * t
        x = xs + shift * t
        pts.append([x, _ring_y(x) + rho * math.sin(a), rho * math.cos(a)])
    i_rt = len(pts) - 1
    xe = xs + shift
    cx, cz = xs, rho
    rho2 = 2 * R + 0.03
    core, ys, ye, i_r, i_t = _clove_core(0.0, 0.0, rho2, 2.3 * R, 'clove')
    sy = -1 if toward_ring else 1
    core = [[cx - p[0], yc + sy * p[1], cz + p[2]] for p in core]
    y_in = yc + sy * ys
    if toward_ring:
        pts += [[xe + 0.1, 0.05, -0.22], [xe + 0.5, -0.6, -0.1], [cx + 1.05, yc - 0.5, cz + 0.3],
                [cx + 1.0, y_in, cz + rho2], [cx + 0.5, y_in, cz + rho2]]
    else:
        pts += [[xe + 0.05, 0.05, -0.2], [xe + 0.4, -0.45, 0.1], [cx + 1.05, y_in, cz + rho2], [cx + 0.5, y_in, cz + rho2]]
    i_down = len(pts) - 1
    pts += [[cx, y_in, cz + rho2]]
    s0 = len(pts)
    if single:
        # one half hitch: round the standing part, across over itself, and away
        pts += core[:i_r + 26]
        last = pts[-1]
        pts += [[last[0] - 0.35, last[1] - 0.25, last[2] - 0.05], [cx - 0.9, yc - 0.9, 0.3], [cx - 1.0, yc - 1.8, 0.3]]
        pts = _dedupe(pts)
        return {'ropes': [{'color': 'b', 'pts': pts}], 'code': None,
                'objects': [{'type': 'ring', 'c': [RING_C[0], RING_C[1], 0], 'radius': RING_R, 'tube': RING_T}],
                'marks': {'stand': (0, k0), 'turn': (0, i_rt), 'down': (0, i_down), 'end': (0, len(pts) - 1)}}
    pts += core
    i_hh1 = s0 + i_r + 26
    y_out = yc + sy * ye
    if toward_ring:
        pts += [[cx - 0.5, y_out, cz + rho2], [cx - 0.85, y_out + 0.25, cz + rho2 * 0.8], [cx - 0.95, y_out + 0.75, 0.32],
                [cx - 0.95, y_out + 1.05, 0.32]]
    else:
        pts += [[cx - 0.5, y_out, cz + rho2], [cx - 0.95, yc - 0.3, cz + rho2 * 0.7], [cx - 1.1, yc - 1.2, 0.3],
                [cx - 1.15, yc - 2.0, 0.3]]
    pts = _dedupe(pts)
    return {'ropes': [{'color': 'a', 'pts': pts}], 'code': None,
            'objects': [{'type': 'ring', 'c': [RING_C[0], RING_C[1], 0], 'radius': RING_R, 'tube': RING_T}],
            'marks': {'stand': (0, k0), 'turn': (0, i_rt), 'down': (0, i_down), 'hh1': (0, i_hh1), 'end': (0, len(pts) - 1)}}


def round_turn_two_half_hitches():
    return _ring_hitch(1.5)


def two_half_hitches():
    return _ring_hitch(0.5)


def half_hitch():
    return _ring_hitch(0.5, single=True)


def buntline_hitch():
    return _ring_hitch(0.5, toward_ring=True, yc=-1.6)


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


def timber_hitch():
    """Round a vertical pole: the rope goes round the pole, the end takes a turn
    round the standing part, then is twisted three times round its own turn."""
    rho = WRAP
    lift = 0.34
    P = math.pi
    S = [[-3.2, 0.0, 1.25], [-2.2, 0.0, 0.95], [-1.3, 0.0, 0.52], [-0.85, 0.0, 0.2]]
    zc = rho + lift

    def chord(a, t):
        d = a + 2 * P
        flat = zc / math.cos(d) if abs(d) < 1.2 else rho
        w = 1.0 if abs(d) <= 0.6 else max(0.0, 1 - (abs(d) - 0.6) / 0.6)
        w = w * w * (3 - 2 * w)
        return rho + (flat - rho) * w
    loop = coil_y(0, 0, rho, -0.5 * P, -2 * P - 0.75, 0.0, 0.0, n=44, rho_fn=chord)
    k_loop = len(S) + len(loop) - 1
    around = [[-0.95, 0.06, zc], [-1.22, 0.4, 0.75], [-1.32, 0.05, 0.18], [-1.2, -0.38, 0.5], [-0.92, -0.34, zc]]
    k_around = k_loop + len(around)
    dog = coil_x(0.0, zc, 2 * R + 0.03, 1.5 * P, 1.5 * P + 6 * P, -0.42, 0.42, n=72)
    tail = [[0.95, -0.36, zc - 0.05], [1.8, -0.42, zc - 0.15], [2.7, -0.48, zc - 0.25]]
    pts = _dedupe(S + loop + around + dog + tail)
    return {'ropes': [{'color': 'c', 'pts': pts}], 'code': None,
            'objects': [{'type': 'pole', 'axis': 'y', 'c': [0, 0, 0], 'radius': POLE, 'len': 3.4}],
            'marks': {'stand': (0, len(S) - 1), 'loop': (0, k_loop), 'around': (0, k_around),
                      'end': (0, len(pts) - 1)}}


# ------------------------------------------------------------------ wave 3: bends

def fishermans_knot():
    """Each rope ties an overhand knot round the other; the knots slide together."""
    off = 2 * R + 0.02
    rho = off + 2 * R + 0.04
    half, i_coil = _fisher_half(1, off, rho)
    A = [[-3.6, 0, 0], [-2.4, 0, 0], [-1.2, 0, 0], [-0.55, 0, 0]] + half
    A = _dedupe(A)
    B = [[-p[0], -p[1], p[2]] for p in A]
    k0 = 4
    return {'ropes': [{'color': 'a', 'pts': A}, {'color': 'b', 'pts': B}], 'code': None, 'objects': [],
            'closure': [(0, 1), (1, -1)],
            'marks': {'a_lay': (0, k0), 'a_coil': (0, k0 + i_coil), 'a_tuck': (0, len(A) - 1),
                      'b_lay': (1, k0), 'b_coil': (1, k0 + i_coil), 'b_tuck': (1, len(B) - 1)}}


def water_knot():
    """Ring bend: an overhand in one end, followed back in reverse by the other end."""
    import numpy as np
    base = [[-3.6, 0.0], [-2.2, 0.0], [-1.0, 0.0], [0.0, 0.02], [0.55, 0.27], [0.82, 0.75], [0.58, 1.22], [0.0, 1.32],
            [-0.5, 1.02], [-0.56, 0.42], [-0.4, -0.3], [-0.05, -0.62], [0.32, -0.45], [0.36, 0.12], [0.4, 0.55],
            [0.95, 0.8], [1.6, 0.78], [2.6, 0.7], [3.6, 0.66]]
    base = _scale(base, 2.2, 4.2)
    A, _, B = _doubled(base, 'uou', z_gain=1.3)
    n = len(A)
    cut = int(n * 0.12)
    a = A[:n - cut][::3].tolist()              # yellow: standing part left, short tail right
    b = B[cut:][::-3].tolist()                 # blue: standing part right, short tail left
    return {'ropes': [{'color': 'a', 'pts': _dedupe(a)}, {'color': 'b', 'pts': _dedupe(b)}], 'code': None, 'objects': [],
            'marks': {'a': (0, len(_dedupe(a)) - 1), 'b': (1, len(_dedupe(b)) - 1)},
            'rope_fractions': {'b_in': (1, 0.3), 'b_half': (1, 0.62)}}





def blood_knot():
    """Barrel knot joining two lines: each end twists round the other line five
    times and comes back through the gap where the lines cross, the two ends going
    through in opposite directions."""
    oy = 0.19                     # the two lines run side by side at y = -oy (yellow) and +oy (blue)
    rho = 2 * R + 0.04
    turns, pitch = 5, 2 * R + 0.06
    x0 = 0.42
    x1 = x0 + turns * pitch
    P = math.pi
    # yellow: standing part from the left, across the centre, wraps round the blue line on the right
    A = [[-4.2, -oy, 0], [-2.8, -oy, 0], [-1.2, -oy, 0], [-0.35, -oy, 0], [0.1, -oy + 0.05, 0.12],
         [x0 - 0.12, oy - rho * 0.7, rho * 0.72]]
    k0 = 4
    m = 18 * turns
    for k in range(m + 1):
        t = k / m
        a = 0.25 * P + 2 * P * turns * t                      # coil_x convention: a=0 front, pi/2 top
        A.append([x0 + (x1 - x0) * t, oy + rho * math.sin(a), rho * math.cos(a)])
    i_coil = len(A) - 1
    # back over the top of the wraps to the centre, then down through the gap
    top = oy + rho + 2 * R + 0.02
    A += [[x1 + 0.22, oy + rho * 0.8, 0.12], [x1 - 0.05, top, 0.0], [(x0 + x1) / 2, top, 0.0], [x0 - 0.05, top, 0.0],
          [-0.08, 0.45, 0.05], [-0.15, 0.12, 0.38], [-0.2, 0.0, 0.0], [-0.22, -0.12, -0.38], [-0.2, -0.6, -0.42],
          [-0.12, -1.1, -0.36], [-0.05, -1.5, -0.3]]
    A = _dedupe(A)
    # blue: the same shape turned half round about the vertical axis, so it enters from the right
    B = [[-p[0], -p[1], -p[2]] for p in A]
    # the blue end must pass through the gap the other way (from below): mirror its tuck in y
    return {'ropes': [{'color': 'a', 'pts': A}, {'color': 'b', 'pts': B}], 'code': None, 'objects': [],
            'marks': {'a_lay': (0, k0), 'b_lay': (1, k0), 'a_coil': (0, i_coil), 'a_tuck': (0, len(A) - 1),
                      'b_coil': (1, i_coil), 'b_tuck': (1, len(B) - 1)}}


def _blood_half(tuck_tail=True):
    """Barrel knot joining two lines: each end twists round the other line five
    times and comes back through the gap where the lines cross, the two ends going
    through in opposite directions."""
    oy = 0.19                     # the two lines run side by side at y = -oy (yellow) and +oy (blue)
    rho = 2 * R + 0.04
    turns, pitch = 5, 2 * R + 0.06
    x0 = 0.42
    x1 = x0 + turns * pitch
    P = math.pi
    # yellow: standing part from the left, across the centre, wraps round the blue line on the right
    A = [[-4.2, -oy, 0], [-2.8, -oy, 0], [-1.2, -oy, 0], [-0.35, -oy, 0], [0.1, -oy + 0.05, 0.12],
         [x0 - 0.12, oy - rho * 0.7, rho * 0.72]]
    k0 = 4
    m = 18 * turns
    for k in range(m + 1):
        t = k / m
        a = 0.25 * P + 2 * P * turns * t                      # coil_x convention: a=0 front, pi/2 top
        A.append([x0 + (x1 - x0) * t, oy + rho * math.sin(a), rho * math.cos(a)])
    i_coil = len(A) - 1
    # back over the top of the wraps to the centre, then down through the gap
    top = oy + rho + 2 * R + 0.02
    A += [[x1 + 0.22, oy + rho * 0.8, 0.12], [x1 - 0.05, top, 0.0], [(x0 + x1) / 2, top, 0.0], [x0 - 0.05, top, 0.0],
          [-0.08, 0.45, 0.05], [-0.15, 0.12, 0.38], [-0.2, 0.0, 0.0], [-0.22, -0.12, -0.38], [-0.2, -0.6, -0.42],
          [-0.12, -1.1, -0.36], [-0.05, -1.5, -0.3]]
    A = _dedupe(A)
    return A, k0, i_coil


def blood_dropper_loop():
    """A loop standing out from the middle of a line: the two sides are twisted round
    each other and the loop is pushed through the gap in the middle of the twists."""
    A, k0, i_coil = _blood_half()
    # cut yellow just after it passes through the gap, then turn it down into the loop
    cut = len(A) - 1
    while cut > 0 and A[cut][2] < -0.2:
        cut -= 1
    a_main = A[:cut + 1]
    B = [[-p[0], -p[1], p[2]] for p in a_main]          # the other side, turned half round
    leg_a = [[-0.25, -0.15, -0.55], [-0.35, -0.6, -0.8], [-0.4, -1.5, -0.8]]
    leg_b = [[0.25, 0.15, -0.55], [0.35, -0.3, -0.95], [0.4, -1.5, -0.95]]
    u = [[-0.35, -2.3, -0.85], [0.0, -2.75, -0.88], [0.35, -2.3, -0.92]]
    pts = _dedupe(a_main + leg_a + u + leg_b[::-1] + B[::-1])
    return {'ropes': [{'color': 'c', 'pts': pts}], 'code': None, 'objects': [], 'relax': 'repel', 'wrapped': True,
            'view': {'elev': 10}, 'marks': {'wraps': (0, i_coil), 'end': (0, len(pts) - 1)}}



# ------------------------------------------------------------------ wave 3: lashings

LP = 0.3                    # lashing pole radius
LW = LP + R + 0.015         # rope centre distance from a lashing pole axis


def _clove_at(cx, cy, cz, flip_x=False, rotate=None):
    """A clove hitch round a vertical pole at (cx, cz), centred on height cy.
    Returns (points, (approach height, exit height))."""
    core, ys, ye, i_r, i_t = _clove_core(0.0, 0.0, LW, 2.3 * R, 'clove')
    sx = -1 if flip_x else 1
    pts = [[cx + sx * p[0], cy + p[1], cz + p[2]] for p in core]
    return pts, (cy + ys, cy + ye)


def _racetrack(xs, rho, y0, n_turns, pitch, u0=0.125, m_per=44):
    """Turns round two parallel vertical poles at x=-xs and x=+xs, rising."""
    P = math.pi
    out = []
    m = m_per * n_turns
    for k in range(m + 1):
        t = k / m
        u = (u0 + t * n_turns) % 1.0
        y = y0 + pitch * n_turns * t
        if u < 0.25:
            p = [-xs + 2 * xs * (u / 0.25), y, rho]
        elif u < 0.5:
            a = (u - 0.25) / 0.25 * P
            p = [xs + rho * math.sin(a), y, rho * math.cos(a)]
        elif u < 0.75:
            p = [xs - 2 * xs * ((u - 0.5) / 0.25), y, -rho]
        else:
            a = P + (u - 0.75) / 0.25 * P
            p = [-xs + rho * math.sin(a), y, rho * math.cos(a)]
        out.append(p)
    return out


def sheer_lashing():
    """Two parallel poles: clove hitch on one, turns round both, frapping turns
    between them, clove hitch on the other."""
    xs = 0.5
    cy1 = -2.5
    c1, (ya, ye) = _clove_at(-xs, cy1, 0.0)
    tail = [[-2.4, ya, LW], [-1.7, ya, LW], [-xs - 0.7, ya, LW], [-xs, ya, LW]]
    pts = tail + c1
    k_clove = len(pts) - 1
    n_turns, pitch = 6, 2 * R + 0.05
    y0 = cy1 + 1.7
    pts += [[-xs + 0.4, ye, LW], [-xs + 0.25, ye + 0.35, LW + 0.32], [-xs + 0.05, cy1 + 0.75, LW + 0.32], [-xs + 0.1, y0 - 0.35, LW + 0.1]]
    turns = _racetrack(xs, LW, y0, n_turns, pitch, u0=0.05)
    pts += turns
    k_turns = len(pts) - 1
    ytop = turns[-1][1]
    ylo, yhi = y0 - 0.36, ytop + 0.4
    zf = LW + 2 * R + 0.12
    pts += [[0.2, ytop + 0.12, LW + 0.12], [0.06, yhi - 0.05, zf * 0.8]]
    frap = []
    for j in range(2):
        e = j * (2 * R + 0.12)
        frap += [[0.0, yhi + e, zf + e], [0.0, (yhi + ylo) / 2, zf + e + 0.02], [0.0, ylo - e, zf + e],
                 [0.0, ylo - e - 0.06, 0.0], [0.0, ylo - e, -zf - e], [0.0, (yhi + ylo) / 2, -zf - e - 0.02],
                 [0.0, yhi + e, -zf - e], [0.0, yhi + e + 0.06, 0.0]]
    pts += frap
    k_frap = len(pts) - 1
    cy2 = yhi + 0.42 + 0.58 + 0.7
    c2, (ya2, ye2) = _clove_at(xs, cy2, 0.0)
    el = 2 * R + 0.12
    pts += [[0.0, yhi + el + 0.42, 0.25], [-0.05, ya2 - 0.25, LW + 0.25], [xs * 0.35, ya2, LW + 0.08], [xs, ya2, LW]] + c2[1:] + [[xs + 0.7, ye2, LW], [xs + 1.4, ye2, LW]]
    pts = _dedupe(pts)
    objs = [{'type': 'pole', 'axis': 'y', 'c': [-xs, 0, 0], 'radius': LP, 'len': 8.0},
            {'type': 'pole', 'axis': 'y', 'c': [xs, 0, 0], 'radius': LP, 'len': 8.0}]
    return {'ropes': [{'color': 'b', 'pts': pts}], 'code': None, 'objects': objs, 'relax': 'gaps',
            'marks': {'clove': (0, k_clove), 'turns': (0, k_turns), 'frap': (0, k_frap), 'end': (0, len(pts) - 1)}}


def square_lashing():
    """Vertical pole behind a horizontal one. Clove hitch on the upright below the
    crossbar, three wrapping turns, two frapping turns between the poles, clove
    hitch on the crossbar."""
    zH = LP + LP + 0.52                       # crossbar centre in front of the upright, leaving a gap
    s = 2 * R + 0.04
    zf0 = zH + LW
    cy1 = -3.3
    c1, (ya, ye) = _clove_at(0.0, cy1, 0.0)
    pts = [[-2.2, ya, LW], [-1.5, ya, LW], [-0.8, ya, LW], [0.0, ya, LW]] + c1
    k_clove = len(pts) - 1
    xr0, yt0 = LW + 0.05, LP + R + 0.06
    pts += [[0.45, ye, LW + 0.05], [xr0 - 0.05, ye + 0.4, LW + 0.5], [xr0 - 0.12, -2.3, 1.0], [xr0 - 0.15, -yt0 - 0.55, zf0 * 0.85], [xr0 - 0.05, -yt0 - 0.15, zf0]]
    for k in range(3):
        xr, yt = xr0 + k * s, yt0 + k * s
        zf, zb = zf0 + k * s, -LW - k * s
        rv = LW + k * s
        c45 = 0.7071 * rv
        side = max(xr * 0.7, LW + 0.03)
        pts += [[xr, -yt, zf], [xr, 0.0, zf + 0.02], [xr, yt, zf],          # up in front of the crossbar, right
                [xr, yt, 0.55 * zf], [side, yt, 0.0], [c45, yt, -c45], [0.0, yt, zb],   # behind the upright, high
                [-c45, yt, -c45], [-side, yt, 0.0], [-xr, yt, 0.55 * zf],
                [-xr, yt, zf], [-xr, 0.0, zf + 0.02], [-xr, -yt, zf],       # down in front, left
                [-xr, -yt, 0.55 * zf], [-side, -yt, 0.0], [-c45, -yt, -c45], [0.0, -yt, zb],  # behind, low
                [c45, -yt, -c45], [side, -yt, 0.0], [xr + 0.5 * s, -yt - 0.5 * s, 0.55 * zf]]
    k_wraps = len(pts) - 1
    zg = zH / 2                                  # middle of the gap between the poles
    half = xr0 + 2 * s + 0.55
    frap = []
    for j in range(2):
        h = half + j * (s + 0.1)
        c = 0.32
        frap += [[h, -h * 0.4, zg], [h, h - c, zg], [h - c * 0.3, h - c * 0.3, zg], [h - c, h, zg],
                 [-h + c, h, zg], [-h + c * 0.3, h - c * 0.3, zg], [-h, h - c, zg],
                 [-h, -h + c, zg], [-h + c * 0.3, -h + c * 0.3, zg], [-h + c, -h, zg], [h * 0.9, -h, zg]]
    pts += [[xr0 + 2 * s + 0.2, -yt0 - 2 * s - 0.3, zg + 0.2]] + frap
    k_frap = len(pts) - 1
    # finish: clove hitch on the crossbar, to the right
    core, ys, ye2, i_r, i_t = _clove_core(0.0, 0.0, LW, 2.3 * R, 'clove')
    cxH = 3.75
    c2 = [[cxH + p[1], -p[0], zH + p[2]] for p in core]      # axis turned to x; approach heads down the front
    hm = half + s + 0.1
    pts += [[hm + 0.3, -hm - 0.1, zg], [hm + 0.42, -0.9, zg - 0.05], [hm + 0.45, 0.0, zg - 0.08], [hm + 0.6, 0.85, zH - 0.1], [cxH + ys - 0.2, 0.95, zH + 0.15], [cxH + ys, 0.9, zH + LW], [cxH + ys, 0.0, zH + LW]] + c2 + \
           [[cxH + ye2, -0.8, zH + LW], [cxH + ye2, -1.6, zH + LW]]
    pts = _dedupe(pts)
    objs = [{'type': 'pole', 'axis': 'y', 'c': [0, 0, 0], 'radius': LP, 'len': 8.0},
            {"type": "pole", "axis": "x", "c": [0, 0, zH], "radius": LP, "len": 9.4}]
    return {'ropes': [{'color': 'c', 'pts': pts}], 'code': None, 'objects': objs, 'relax': 'gaps',
            'marks': {'clove': (0, k_clove), 'wraps': (0, k_wraps), 'frap': (0, k_frap), 'end': (0, len(pts) - 1)}}


# ------------------------------------------------------------------ wave 3: fishing knots on a hook

EYE_C, EYE_R, EYE_T = (0.0, 0.5), 0.34, 0.07
SHANK_R = 0.08


def _hook():
    """A hook drawn large: eye at the top, shank down, bend and point."""
    return [{'type': 'ring', 'c': [EYE_C[0], EYE_C[1], 0], 'radius': EYE_R, 'tube': EYE_T},
            {'type': 'pole', 'axis': 'y', 'c': [0, -1.54, 0], 'radius': SHANK_R, 'len': 3.32, 'metal': True},
            {'type': 'arc', 'c': [0.75, -3.2, 0], 'radius': 0.75, 'tube': SHANK_R, 'a0': math.pi, 'a1': 2 * math.pi},
            {'type': 'pole', 'axis': 'y', 'c': [1.5, -2.75, 0], 'radius': SHANK_R, 'len': 0.9, 'metal': True}]


def _clinch(improved=False, turns=5):
    """Line through the eye, the tag end twisted round the standing line, back
    through the small loop by the eye (and, improved, back through the big loop)."""
    ey = EYE_C[1]
    zs = 0.2                                   # standing line runs just in front of the eye plane
    pitch = 2 * R + 0.06
    y0 = ey + EYE_R + 0.75                     # wraps start above the small loop
    rho = 2 * R + 0.03
    pts = [[0.05, 6.4, zs], [0.03, 5.0, zs], [0.0, y0 + 0.3, zs], [0.0, ey + 0.5, zs + 0.12], [0.0, ey + 0.05, 0.08],
           [0.0, ey - 0.08, -0.25], [0.02, ey + 0.35, -0.42], [0.08, y0 - 0.45, -0.38]]
    k_eye = 5
    k_up = len(pts) - 1
    m = 22 * turns
    for k in range(m + 1):
        t = k / m
        a = math.pi + 2 * math.pi * turns * t           # starts behind the standing line
        pts.append([rho * math.sin(a), y0 + pitch * turns * t, zs + rho * math.cos(a)])
    k_wraps = len(pts) - 1
    ytop = pts[-1][1]
    # back down outside the wraps, on the right, to the small loop just above the eye
    out = rho + 2 * R + 0.06
    pts += [[out * 0.55, ytop + 0.32, zs + 0.15], [out * 1.05, ytop - 0.2, zs], [out, ytop - 0.6, zs], [out, y0 + 0.2, zs], [out * 0.9, ey + 0.95, 0.0],
            [0.35, ey + 0.82, -0.08], [0.0, ey + 0.8, -0.1], [-0.4, ey + 0.82, -0.08]]
    k_tuck = len(pts) - 1
    if improved:
        # back up through the big loop: between the return strand and the wraps, on the right
        pts += [[-0.75, ey + 1.0, 0.05], [-0.7, ey + 1.3, 0.45], [-0.1, ey + 1.2, zs + 0.55], [out * 0.55, y0 - 0.25, zs + 0.35],
                [out * 0.82, y0 - 0.2, -0.02], [out * 0.95, y0 - 0.05, -0.45], [out + 0.5, y0 + 0.05, -0.6]]
    else:
        pts += [[-0.8, ey + 0.9, 0.0], [-1.3, ey + 1.05, 0.05]]
    pts = _dedupe(pts)
    return {'ropes': [{'color': 'c' if improved else 'a', 'pts': pts}], 'code': None, 'objects': _hook(),
            'marks': {'eye': (0, k_eye), 'up': (0, k_up), 'wraps': (0, k_wraps), 'tuck': (0, k_tuck), 'end': (0, len(pts) - 1)}}


def clinch_knot():
    return _clinch(False)


def improved_clinch_knot():
    return _clinch(True)


def _double_3d(base, d=None, n0=(1.0, 0.0, 0.0)):
    """Offset a 3D path both ways with a rotation-minimising frame.
    Returns (A, B) as numpy arrays (same length as the resampled base)."""
    import numpy as np
    from knotlib import catmull_rom, resample
    P, _ = resample(catmull_rom(base, per_seg=12), 0.04)
    d = d or (R + 0.025)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    n = np.array(n0, float)
    n -= n.dot(T[0]) * T[0]
    n /= np.linalg.norm(n)
    N = [n]
    for i in range(1, len(P)):
        n = N[-1] - N[-1].dot(T[i]) * T[i]
        n /= np.linalg.norm(n)
        N.append(n)
    N = np.array(N)
    return P + d * N, P - d * N, N





def flat_overhand_bend():
    """Offset overhand bend: the two ends laid side by side and tied together in one
    overhand knot, both tails on the same side."""
    base = [[-3.6, 0.0], [-2.2, 0.0], [-1.0, 0.0], [0.0, 0.02], [0.55, 0.27], [0.82, 0.75], [0.58, 1.22], [0.0, 1.32],
            [-0.5, 1.02], [-0.56, 0.42], [-0.4, -0.3], [-0.05, -0.62], [0.32, -0.45], [0.36, 0.12], [0.4, 0.55],
            [0.95, 0.8], [1.6, 0.78], [2.3, 0.72]]
    base = _scale(base, 2.3, 4.2)
    A, _, B = _doubled(base, 'uou', z_gain=1.35)
    a = _dedupe(A[::3].tolist() + [A[-1].tolist()])
    b = _dedupe(B[::3].tolist() + [B[-1].tolist()])
    from knotlib import ctrl_arc_positions
    cs = ctrl_arc_positions(base)
    fr = {k: cs[i] / cs[-1] for k, i in (('start', 3), ('loop', 10), ('tuck', 15))}
    return {'ropes': [{'color': 'a', 'pts': a}, {'color': 'b', 'pts': b}], 'code': None, 'objects': [],
            'fractions': fr, 'marks': {'a': (0, len(a) - 1), 'b': (1, len(b) - 1)}}


# ------------------------------------------------------------------ wave 4: generated decorative knots

def _alternating_heights(P):
    """Given a dense planar closed or open curve P (N,3 with z=0), make every
    crossing alternate over/under along the curve. Returns P with z set."""
    import numpy as np
    from knotlib import find_crossings, z_profile, LIFT
    cr = find_crossings([P])
    passes = []
    for ci, c in enumerate(cr):
        passes.append((c['ia'], ci))
        passes.append((c['ib'], ci))
    passes.sort()
    status = {}
    targets = []
    ok = True
    for k, (f, ci) in enumerate(passes):
        over = (k % 2 == 0)
        if ci in status and status[ci] == over:
            ok = False
        status.setdefault(ci, over)
        targets.append((f, LIFT if over else -LIFT))
    Q = P.copy()
    Q[:, 2] = z_profile(len(P), targets)
    return Q, len(cr), ok


def _turks_head_planar(L, B, r0=2.2, amp=0.95, n=None):
    """Annulus drawing of the L-lead, B-bight Turk's head: r = r0 + amp cos(B t / L),
    angle t, t from 0 to 2 pi L, then alternating over/under."""
    import numpy as np
    from knotlib import resample
    n = n or 220 * L
    t = np.linspace(0, 2 * math.pi * L, n + 1)
    r = r0 + amp * np.cos(B * t / L)
    P = np.column_stack([r * np.cos(t), r * np.sin(t), np.zeros_like(t)])
    P, _ = resample(P, 0.03)
    return _alternating_heights(P), t


LIFT_TH = 0.17


def _turks_head(L, B, color, pr_extra=0.0):
    """Turk's head wrapped round a pole (axis y): the annulus drawing rolled onto
    the cylinder, its radial offset becoming the axial position."""
    import numpy as np
    (Q, ncross, ok), _ = _turks_head_planar(L, B)
    r0, amp = 2.2, 0.95
    pr = 0.55 + 0.17 * B + pr_extra              # pole radius grows with the number of bights
    rho0 = pr + R + 0.02
    band = 0.45 + 0.33 * L                        # half-height of the band on the pole
    pts = []
    for q in Q:
        ang = math.atan2(q[1], q[0])
        rr = math.hypot(q[0], q[1])
        y = (rr - r0) / amp * band
        rho = rho0 + LIFT_TH + q[2]
        pts.append([rho * math.sin(ang), y, rho * math.cos(ang)])
    pts = pts[::2] + [pts[0]]
    return {'ropes': [{'color': color, 'pts': pts, 'closed': True}], 'code': None,
            'objects': [{'type': 'pole', 'axis': 'y', 'c': [0, 0, 0], 'radius': pr, 'len': 2 * band + 2.4}],
            'jones_ropes': [Q], 'closure': [(0, 1)], 'relax': 'repel', 'wrapped': True,
            'fractions': {'q1': 0.25, 'q2': 0.5, 'q3': 0.75}, 'marks': {'end': (0, len(pts) - 1)},
            'alternating': ok, 'ncross': ncross}


def turks_head_3l4b():
    return _turks_head(3, 4, 'b')


def turks_head_4l5b():
    return _turks_head(4, 5, 'c')


def turks_head_5l4b():
    return _turks_head(5, 4, 'a', pr_extra=0.3)


def carrick_bend():
    """The 3-lead 4-bight Turk's head drawn flat (the carrick mat), cut open at two
    opposite outer bights: two ropes, each entering on one side and leaving on the other."""
    import numpy as np
    (Q, n, ok), _ = _turks_head_planar(3, 4, r0=1.9, amp=0.95)
    ang = np.unwrap(np.arctan2(Q[:, 1], Q[:, 0]))
    ang -= ang[0]
    N = len(Q)
    i1 = int(np.argmin(np.abs(ang - 3 * math.pi)))
    gap = 7
    def tail(p, outward, along, length=2.4, zt=0.0):
        out = []
        for k in range(1, 6):
            t = k / 5
            out.append([p[0] + outward[0] * length * t + along[0] * 0.5 * t, p[1] + outward[1] * length * t + along[1] * 0.5 * t,
                        p[2] + (zt - p[2]) * min(1, 2 * t)])
        return out
    def end_tail(P, i, sign):
        p = P[i]
        r = np.array([p[0], p[1]]) / np.hypot(p[0], p[1])
        t = P[min(i + 1, len(P) - 1), :2] - P[max(i - 1, 0), :2]
        t = t / np.linalg.norm(t) * sign
        return tail(p, r * 0.9 + t * 0.45, t, 2.0, zt=0.19 * sign)
    a = Q[gap:i1 - gap]
    b = np.vstack([Q[i1 + gap:], Q[1:N - 0 if gap == 0 else 1]])[: (N - 1) - (i1 + gap) + 0]
    b = np.vstack([Q[i1 + gap:N - 1], Q[0:1]])[:-gap] if False else Q[i1 + gap:N - 1 - gap]
    A = end_tail(a, 0, -1)[::-1] + a[::3].tolist() + end_tail(a, len(a) - 1, 1)
    Bp = end_tail(b, 0, -1)[::-1] + b[::3].tolist() + end_tail(b, len(b) - 1, 1)
    A = [[p[0] * 1.15, p[1], p[2]] for p in A]
    Bp = [[p[0] * 1.15, p[1], p[2]] for p in Bp]
    return {'ropes': [{'color': 'a', 'pts': _dedupe(A)}, {'color': 'b', 'pts': _dedupe(Bp)}], 'code': None, 'objects': [],
            'closure': [(0, 1), (1, 1)], 'relax': 'gaps',
            'marks': {'a': (0, len(_dedupe(A)) - 1), 'b': (1, len(_dedupe(Bp)) - 1)},
            'rope_fractions': {'b1': (1, 0.35), 'b2': (1, 0.65)}}


def monkeys_fist(turns=3):
    """Three bands of turns at right angles, woven round a ball: the second set
    goes round the first; the third goes inside the first and round the second."""
    s = 2 * R + 0.08
    ri = 1.05
    ro = ri + 2 * R + 0.1
    P = math.pi
    def helix(axis, k0, k1, a0, rfun, n=None):
        n = n or 40 * turns
        out = []
        for k in range(n + 1):
            t = k / n
            a = a0 + 2 * P * turns * t
            off = k0 + (k1 - k0) * t
            rr = rfun(a)
            if axis == 'x':
                out.append([off, rr * math.sin(a), rr * math.cos(a)])
            elif axis == 'y':
                out.append([rr * math.sin(a), off, rr * math.cos(a)])
            else:
                out.append([rr * math.cos(a), rr * math.sin(a), off])
        return out
    span = s * (turns - 1) / 2
    # A: round the x axis; outer on the y faces, inner on the z faces
    A = helix('x', -span, span, -0.5 * P, lambda a: ri + (ro - ri) * math.sin(a) ** 2)
    # B: round the y axis; outer on the z faces, inner on the x faces
    B = helix('y', -span, span, 0.0, lambda a: ro - (ro - ri) * math.sin(a) ** 2)
    # C: round the z axis; outer on the x faces, inner on the y faces
    C = helix('z', -span, span, 0.0, lambda a: ro - (ro - ri) * math.sin(a) ** 2)
    import numpy as np

    def over(p, q, rout, n=8):
        p, q = np.array(p, float), np.array(q, float)
        up, uq = p / np.linalg.norm(p), q / np.linalg.norm(q)
        om = math.acos(max(-1.0, min(1.0, float(up.dot(uq)))))
        out = []
        for k in range(1, n):
            t = k / n
            if om < 1e-6:
                u = up
            else:
                u = (math.sin((1 - t) * om) * up + math.sin(t * om) * uq) / math.sin(om)
            rr = (1 - t) * np.linalg.norm(p) + t * np.linalg.norm(q) + (rout - max(np.linalg.norm(p), np.linalg.norm(q))) * math.sin(math.pi * t)
            out.append((u * rr).tolist())
        return out
    rout = ro + 2 * R + 0.12
    wB = [0.0, -span - 0.75, rout]                 # approach each set from its own outside edge
    wC = [rout, 0.0, -span - 0.75]
    j1 = [[-span * 0.2 + span * 1.2 + 0.3, -rout, -0.3]] + over([span + 0.3, -rout, -0.35], wB, rout, 7) + [wB]
    j2 = [[0.0, span + 0.5, rout]] + over([0.0, span + 0.55, rout], wC, rout, 7) + [wC]
    stand = [[-span - 0.6, -3.6, 0.0], [-span - 0.6, -2.6, 0.0], [-span - 0.55, -rout - 0.25, 0.0]]
    tail = [[rout, 0.0, span + 0.55], [rout * 0.7, -rout * 0.7, span + 0.6], [0.3, -2.4, span + 0.6], [0.3, -3.3, span + 0.6]]
    pts = _dedupe(stand + A + j1 + B + j2 + C + tail)
    kA = len(stand) + len(A)
    kB = kA + len(j1) + len(B)
    return {'ropes': [{'color': 'b', 'pts': pts}], 'code': None, 'objects': [], 'wrapped': True, 'relax': 'repel',
            'view': {'elev': 25}, 'marks': {'a': (0, kA), 'b': (0, kB), 'end': (0, len(pts) - 1)}}


def _flat_braid(n, rows=None, w=0.5, dy=0.5):
    """n-strand flat braid: alternately from the left and right, the outermost strand
    crosses to the middle, over-under-over the strands it passes."""
    import numpy as np
    from knotlib import catmull_rom, resample, find_crossings, z_profile, LIFT
    rows = rows or (4 * n + 2)
    order = list(range(n))                      # strand at each position
    paths = {s: [[(i - (n - 1) / 2) * w, 0.6]] for i, s in enumerate(order)}
    for s in range(n):
        paths[s].append([paths[s][0][0], 0.0])
    moves = []
    y = 0.0
    for r in range(rows):
        from_left = (r % 2 == 0)
        k = (n - 1) // 2 if from_left else n // 2
        if from_left:
            m = order[0]
            passed = order[1:k + 1]
            order = order[1:k + 1] + [m] + order[k + 1:]
        else:
            m = order[-1]
            passed = list(reversed(order[n - 1 - k:n - 1]))
            order = order[:n - 1 - k] + [m] + order[n - 1 - k:n - 1]
        moves.append((m, passed))
        y -= dy
        for i, s in enumerate(order):
            paths[s].append([(i - (n - 1) / 2) * w, y])
    for s in range(n):
        last = paths[s][-1]
        paths[s].append([last[0] * 1.15, y - 0.6])
        paths[s].append([last[0] * 1.35, y - 1.3])
    ropes = [resample(catmull_rom(paths[s], per_seg=10), 0.03)[0] for s in range(n)]
    cr = find_crossings(ropes)
    targets = [[] for _ in range(n)]
    for c in cr:
        yc = c['xy'][1]
        r = int(math.floor(-yc / dy))
        if r < 0 or r >= rows:
            continue
        m, passed = moves[r]
        a, b = c['ra'], c['rb']
        if m not in (a, b):
            continue
        o = b if a == m else a
        if o not in passed:
            continue
        over = passed.index(o) % 2 == 0
        im = c['ia'] if a == m else c['ib']
        io = c['ib'] if a == m else c['ia']
        targets[m].append((im, LIFT if over else -LIFT))
        targets[o].append((io, -LIFT if over else LIFT))
    out = []
    for s in range(n):
        P = ropes[s].copy()
        P[:, 2] = z_profile(len(P), targets[s])
        out.append(P)
    cols = ['a', 'b', 'c']
    ropes_out = [{'color': cols[s % 3], 'pts': P[::2].tolist() + [P[-1].tolist()]} for s, P in enumerate(out)]
    # reveal by rows: fraction of each strand above a given height
    fl = {}
    for name, rr in (('r1', 2), ('r2', 4), ('r3', 2 * n)):
        yt = -dy * rr - 0.05
        fr = []
        for P in out:
            seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
            sarc = np.concatenate([[0], np.cumsum(seg)])
            idx = np.nonzero(P[:, 1] < yt)[0]
            fr.append(float(sarc[idx[0]] / sarc[-1]) if len(idx) else 1.0)
        fl[name] = fr
    return {'ropes': ropes_out, 'code': None, 'objects': [],
            'fraction_lists': fl, 'marks': {'end': (0, len(ropes_out[0]['pts']) - 1)}, 'ncross': len(cr)}


def flat_braid_3():
    return _flat_braid(3)


def flat_braid_4():
    return _flat_braid(4)


def flat_braid_5():
    return _flat_braid(5)


def flat_braid_6():
    return _flat_braid(6)


def flat_braid_7():
    return _flat_braid(7)


def _laid_strands(n=3, y0=-1.7, y1=0.0, rc=0.19, pitch=1.6):
    """Strands of a laid rope below the knot: n helices round the rope axis."""
    out = []
    for i in range(n):
        ph = 2 * math.pi * i / n
        pts = []
        m = 24
        for k in range(m + 1):
            y = y0 + (y1 - y0) * k / m
            a = ph + 2 * math.pi * (y - y1) / pitch
            pts.append([rc * math.sin(a), y, rc * math.cos(a)])
        out.append(pts)
    return out


def _crown_like(kind='crown', n=3):
    """Crown (ends point down) or wall (ends point up) on an n-strand rope end.
    Built in top view: each strand sweeps round to the next strand's side, and at
    each crossing strand i lies over strand i+1 (crown) or under it (wall)."""
    import numpy as np
    from knotlib import catmull_rom, resample, find_crossings, z_profile, LIFT
    lay = _laid_strands(n)
    P3 = []
    for i in range(n):
        ph = 2 * math.pi * i / n
        path = list(lay[i])
        base = lay[i][-1]
        m = 16
        for k in range(1, m + 1):
            t = k / m
            a = ph + (2 * math.pi / n) * 1.35 * t
            if kind == 'crown':
                r = 0.19 + 0.62 * math.sin(math.pi / 2 * t)
                y = 0.55 * math.sin(math.pi * t) + 0.05
            else:
                r = 0.19 + 0.62 * math.sin(math.pi / 2 * t)
                y = 0.18 * t
            path.append([r * math.sin(a), y, r * math.cos(a)])
        a_end = ph + (2 * math.pi / n) * 1.35
        if kind == 'crown':
            for yy in (-0.15, -0.6, -1.1):
                path.append([0.82 * math.sin(a_end), yy, 0.82 * math.cos(a_end)])
        else:
            a2 = a_end + 0.5
            path += [[0.55 * math.sin(a2), 0.45, 0.55 * math.cos(a2)], [0.3 * math.sin(a2 + 0.3), 0.9, 0.3 * math.cos(a2 + 0.3)],
                     [0.32 * math.sin(a2 + 0.4), 1.6, 0.32 * math.cos(a2 + 0.4)]]
        P3.append(resample(catmull_rom(path, per_seg=10), 0.03)[0])
    # over/under in top view (project onto x-z); "over" = higher y
    top = [np.column_stack([P[:, 0], P[:, 2], P[:, 1]]) for P in P3]
    cr = find_crossings([np.column_stack([T[:, 0], T[:, 1], np.zeros(len(T))]) for T in top])
    targets = [[] for _ in range(n)]
    for c in cr:
        a, b = c['ra'], c['rb']
        if a == b:
            continue
        a_over = (b == (a + 1) % n)
        if kind == 'wall':
            a_over = not a_over
        targets[a].append((c['ia'], LIFT if a_over else -LIFT))
        targets[b].append((c['ib'], -LIFT if a_over else LIFT))
    out = []
    for i, P in enumerate(P3):
        Q = P.copy()
        Q[:, 1] += z_profile(len(Q), targets[i]) * 1.1
        out.append(Q)
    cols = ['a', 'b', 'c']
    ropes = [{'color': cols[i % 3], 'pts': Q[::2].tolist() + [Q[-1].tolist()]} for i, Q in enumerate(out)]
    knot_start = [len(lay[i]) / (len(lay[i]) + 16 + 3) for i in range(n)]
    return {'ropes': ropes, 'code': None, 'objects': [], 'wrapped': True, 'relax': 'repel',
            'fraction_lists': {'unlaid': [0.55] * n, 'one': [1.0] + [0.55] * (n - 1), 'two': [1.0, 1.0] + [0.55] * (n - 2)},
            'marks': {'end': (0, len(ropes[0]['pts']) - 1)}, 'view': {'elev': 38}}


def crown_knot():
    return _crown_like('crown')


def wall_knot():
    return _crown_like('wall')


def carrick_mat():
    """The carrick mat: the 3-lead 4-bight Turk's head laid flat, followed round twice."""
    import numpy as np
    (Q, n, ok), _ = _turks_head_planar(3, 4, r0=2.4, amp=1.25)
    Q[:, 0] *= 1.25
    T = np.gradient(Q[:, :2], axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    N = np.column_stack([-T[:, 1], T[:, 0]])
    d = R + 0.025
    A = np.column_stack([Q[:, :2] + d * N, Q[:, 2] * 1.25])
    B = np.column_stack([Q[:, :2] - d * N, Q[:, 2] * 1.25])
    a = A[::3].tolist() + [A[0].tolist()]
    b = B[::3].tolist() + [B[0].tolist()]
    return {'ropes': [{'color': 'c', 'pts': a, 'closed': True}, {'color': 'c', 'pts': b, 'closed': True}],
            'code': None, 'objects': [], 'jones_ropes': [Q], 'closure': [(0, 1)], 'alternating': ok, 'ncross': n,
            'fraction_lists': {'half': [0.5, 0.0], 'first': [1.0, 0.0], 'second': [1.0, 0.5]},
            'marks': {'end': (0, len(a) - 1)}}


# ------------------------------------------------------------------ wave 5: splices and whippings

RC = 0.19                     # radius of the strand centres in a laid three-strand rope
PITCH = 1.9                   # length of one full turn of the lay (right-hand lay)


def _cyl_weave(parts, r_ann=8.0, first_over=True):
    """Strands on a rope's surface in unrolled form: parts = [{theta, y, base, kind}],
    kind an array of 'lay' / 'tuck' per sample. Crossings are found on an annulus
    drawing (radius r_ann + y, angle theta), a faithful flat picture of the
    cylinder. Along each strand, its tucked stretches go over, under, over... the
    lay strands they meet; where a tuck goes under, the lay strand is lifted."""
    import numpy as np
    from knotlib import find_crossings, z_profile
    ann = [np.column_stack([(r_ann + p['y']) * np.cos(p['theta']), (r_ann + p['y']) * np.sin(p['theta']),
                            np.zeros(len(p['y']))]) for p in parts]
    cr = find_crossings(ann)
    def kind(k, f):
        return parts[k]['kind'][int(round(f))]
    # number each strand's tuck passages in order along the strand
    passes = [[] for _ in parts]
    for ci, c in enumerate(cr):
        ka, kb = kind(c['ra'], c['ia']), kind(c['rb'], c['ib'])
        if ka == 'tuck' and kb == 'lay':
            passes[c['ra']].append((c['ia'], ci))
        if kb == 'tuck' and ka == 'lay':
            passes[c['rb']].append((c['ib'], ci))
    over_at = {}
    for k, p in enumerate(passes):
        for n_, (f, ci) in enumerate(sorted(p)):
            over_at[(k, ci)] = (n_ % 2 == 0) == first_over
    targets = [[] for _ in parts]
    bad = 0
    for ci, c in enumerate(cr):
        if (c['ra'], ci) in over_at:
            t, ti, l, li = c['ra'], c['ia'], c['rb'], c['ib']
        elif (c['rb'], ci) in over_at:
            t, ti, l, li = c['rb'], c['ib'], c['ra'], c['ia']
        else:
            bad += 1
            continue
        if over_at[(t, ci)]:
            targets[t].append((ti, 0.14))
        else:
            targets[l].append((li, TUCK_BASE + 0.31 - RC))
    out = []
    for k, p in enumerate(parts):
        off = z_profile(len(p['y']), targets[k], plateau=1.0 * R / 0.03, ramp=2.6 * R / 0.03)
        rho = p['base'] + off
        out.append(np.column_stack([rho * np.sin(p['theta']), p['y'], rho * np.cos(p['theta'])]))
    return out, len(cr), bad


def _lay(i, y0, y1, n=3, step=0.03):
    import numpy as np
    y = np.arange(y0, y1 + 1e-9, step)
    th = 2 * math.pi * i / n + 2 * math.pi * y / PITCH
    return th, y


def _tuck(theta0, y0, y1, step=0.03, pitch=None):
    """A strand tucked against the lay, running from y0 down to y1."""
    import numpy as np
    pitch = pitch or PITCH * 1.05
    y = np.arange(y0, y1 - 1e-9, -step)
    th = theta0 - 2 * math.pi * (y - y0) / pitch          # opposite hand to the lay
    return th, y


TUCK_BASE = RC + 0.17


def back_splice():
    """Crown the strands, then tuck each one back down the rope against the lay,
    over one strand and under the next, three times."""
    import numpy as np
    n = 3
    parts = []
    for i in range(n):
        th, y = _lay(i, -3.4, 0.0)
        parts.append({'theta': th, 'y': y, 'base': np.full(len(y), RC), 'kind': ['lay'] * len(y)})
    crowns, starts = [], []
    for i in range(n):
        th0 = 2 * math.pi * i / n
        sweep = 2 * math.pi / n * 1.25
        arc = []
        m = 18
        for k in range(1, m + 1):
            t = k / m
            a = th0 + sweep * t
            r = RC + (0.62 - RC) * math.sin(math.pi * t) ** 0.7 + (TUCK_BASE - RC) * t
            yy = 0.5 * math.sin(math.pi * t) - 0.12 * t
            arc.append([r * math.sin(a), yy, r * math.cos(a)])
        crowns.append(arc)
        starts.append(th0 + sweep)
    for i in range(n):
        th, y = _tuck(starts[i], -0.18, -2.5)
        parts.append({'theta': th, 'y': y, 'base': np.full(len(y), TUCK_BASE), 'kind': ['tuck'] * len(y)})
    P3, ncross, bad = _cyl_weave(parts)
    cols = ['a', 'b', 'c']
    ropes = []
    fl = {}
    for i in range(n):
        lay, tuck = P3[i], P3[n + i]
        pts = lay[::3].tolist() + crowns[i] + tuck[::3].tolist()
        ropes.append({'color': cols[i], 'pts': _dedupe(pts)})
    nl = [len(P3[i][::3]) for i in range(n)]
    tot = [len(r['pts']) for r in ropes]
    fl['crowned'] = [(nl[i] + 18) / tot[i] for i in range(n)]
    fl['one'] = [(nl[i] + 18 + (tot[i] - nl[i] - 18) / 3) / tot[i] for i in range(n)]
    fl['two'] = [(nl[i] + 18 + 2 * (tot[i] - nl[i] - 18) / 3) / tot[i] for i in range(n)]
    fl['unlaid'] = [nl[i] / tot[i] for i in range(n)]
    return {'ropes': ropes, 'code': None, 'objects': [], 'wrapped': True, 'relax': 'repel',
            'fraction_lists': fl, 'marks': {'end': (0, len(ropes[0]['pts']) - 1)}, 'ncross': ncross,
            'unresolved': bad, 'view': {'elev': 15}}


def short_splice():
    """Two ropes married end to end: each rope's strands are tucked into the other
    rope against its lay, over one and under one."""
    import numpy as np
    n = 3
    parts = []
    off = math.pi / n                                # the second rope's strands sit between the first's
    for i in range(n):                               # yellow rope from below, its strands tucked upward
        th1, y1 = _lay(i, -3.6, 0.0)
        y2 = np.arange(0.03, 2.55, 0.03)
        th2 = th1[-1] - 2 * math.pi * y2 / (PITCH * 1.05)
        base = np.concatenate([np.full(len(y1), RC), RC + (TUCK_BASE - RC) * np.clip(y2 / 0.25, 0, 1)])
        parts.append({'theta': np.concatenate([th1, th2]), 'y': np.concatenate([y1, y2]), 'base': base,
                      'kind': ['lay'] * len(y1) + ['tuck'] * len(y2)})
    for i in range(n):                               # blue rope from above, its strands tucked downward
        y1 = np.arange(3.6, -1e-9, -0.03)
        th1 = 2 * math.pi * i / n + off + 2 * math.pi * y1 / PITCH
        y2 = np.arange(-0.03, -2.55, -0.03)
        th2 = th1[-1] - 2 * math.pi * y2 / (PITCH * 1.05)
        base = np.concatenate([np.full(len(y1), RC), RC + (TUCK_BASE - RC) * np.clip(-y2 / 0.25, 0, 1)])
        parts.append({'theta': np.concatenate([th1, th2]), 'y': np.concatenate([y1, y2]), 'base': base,
                      'kind': ['lay'] * len(y1) + ['tuck'] * len(y2)})
    P3, ncross, bad = _cyl_weave(parts)
    cols = ['a', 'a', 'a', 'b', 'b', 'b']
    ropes = [{'color': cols[k], 'pts': P[::3].tolist() + [P[-1].tolist()]} for k, P in enumerate(P3)]
    fr_meet = [len(_lay(0, -3.6, 0.0)[1]) / len(P3[0])] * 6
    fl = {'meet': fr_meet, 'yellow': [1.0] * 3 + fr_meet[3:], 'all': [1.0] * 6}
    return {'ropes': ropes, 'code': None, 'objects': [], 'wrapped': True, 'relax': 'repel',
            'fraction_lists': fl, 'marks': {'end': (0, len(ropes[0]['pts']) - 1)}, 'ncross': ncross, 'unresolved': bad,
            'view': {'elev': 10}}


def eye_splice():
    """The end is laid back alongside the rope to form an eye, and its three strands
    are tucked into the standing part against the lay."""
    import numpy as np
    from knotlib import catmull_rom, resample
    n = 3
    ytop = 0.45
    # eye centreline: up from the standing part, round, and back down beside it
    rc_eye, cx, cy = 1.45, 1.45, ytop + 1.7
    cl = [[0, ytop, 0], [0, ytop + 0.6, 0]]
    for k in range(1, 12):
        a = math.pi - (math.pi + 0.55) * k / 11            # from the left, over the top, round to lower right
        cl.append([cx + rc_eye * math.cos(a), cy + rc_eye * math.sin(a), 0])
    cl += [[1.15, ytop + 0.2, 0], [0.82, ytop - 0.15, 0]]
    C, _ = resample(catmull_rom(cl, per_seg=12), 0.03)
    T = np.gradient(C, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    N = [np.array([0.0, 0.0, 1.0])]
    for i in range(1, len(C)):
        v = N[-1] - N[-1].dot(T[i]) * T[i]
        N.append(v / np.linalg.norm(v))
    N = np.array(N)
    Bn = np.cross(T, N)
    arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))])
    parts, eyes = [], []
    for i in range(n):
        th, y = _lay(i, -3.4, ytop)
        parts.append({'theta': th, 'y': y, 'base': np.full(len(y), RC), 'kind': ['lay'] * len(y)})
        psi = th[-1] + 2 * math.pi * arc / PITCH
        E = C + RC * (np.cos(psi)[:, None] * Bn * 0 + np.sin(psi)[:, None] * Bn + np.cos(psi)[:, None] * N)
        eyes.append(E)
    # tucks: each eye strand goes round to its own starting point on the standing part
    tucks, conns = [], []
    starts = [0.5 * math.pi, 0.5 * math.pi + 2 * math.pi / 3, 0.5 * math.pi - 2 * math.pi / 3]
    ends = [E[-1] for E in eyes]
    used = set()
    order = []
    for E in eyes:
        ang = math.atan2(E[-1][0], E[-1][2])
        j = min((j for j in range(n) if j not in used), key=lambda j: abs(((starts[j] - ang + math.pi) % (2 * math.pi)) - math.pi))
        used.add(j)
        order.append(j)
    for i in range(n):
        j = order[i]
        th, y = _tuck(starts[j], ytop - 0.5, -2.4)
        parts.append({'theta': th, 'y': y, 'base': np.full(len(y), TUCK_BASE), 'kind': ['tuck'] * len(y)})
        e = eyes[i][-1]
        a0 = math.atan2(e[0], e[2])
        a1 = starts[j]
        while a1 - a0 > math.pi:
            a1 -= 2 * math.pi
        while a0 - a1 > math.pi:
            a1 += 2 * math.pi
        conn = []
        for k in range(1, 7):
            t = k / 7
            a = a0 + (a1 - a0) * t
            rr = (1 - t) * math.hypot(e[0], e[2]) + t * TUCK_BASE + 0.4 * math.sin(math.pi * t)
            conn.append([rr * math.sin(a), e[1] + (ytop - 0.5 - e[1]) * t, rr * math.cos(a)])
        conns.append(conn)
    P3, ncross, bad = _cyl_weave(parts)
    cols = ['a', 'b', 'c']
    ropes = []
    for i in range(n):
        pts = P3[i][::3].tolist() + eyes[i][::3].tolist() + conns[i] + P3[n + i][::3].tolist()
        ropes.append({'color': cols[i], 'pts': _dedupe(pts)})
    tot = [len(r['pts']) for r in ropes]
    nl = len(P3[0][::3]) + len(eyes[0][::3])
    fl = {'eye': [nl / t for t in tot], 'first': [(nl + 8) / t for t in tot], 'one': [(nl + 8 + (t - nl - 8) / 3) / t for t in tot]}
    return {'ropes': ropes, 'code': None, 'objects': [], 'wrapped': True, 'relax': 'repel',
            'fraction_lists': fl, 'marks': {'end': (0, len(ropes[0]['pts']) - 1)}, 'ncross': ncross, 'unresolved': bad,
            'view': {'elev': 8}}


TW = 0.075                     # twine radius for whippings and seizings
ROPE_R = 0.42                  # radius of the rope being whipped


def common_whipping():
    """Twine laid along the rope in a bight pointing to the end, turns wrapped over it
    toward the end, the end passed through the bight; pulling the other end draws
    the bight under the turns."""
    r = TW
    rl = ROPE_R + r + 0.01                      # lying on the rope
    rt = ROPE_R + 3 * r + 0.04                  # turns over the legs
    leg = 0.12                                  # legs either side of the front line
    al = leg / rl
    P = math.pi
    y_lo, y_hi = -2.3, -0.75
    pts = [[-leg * 1.2, -3.4, rl + 0.05], [-leg, -2.8, rl], [-leg, -1.5, rl], [-leg, -0.6, rl],
           [-leg, -0.32, rl + 0.12], [0.0, -0.16, rl + 0.2], [leg, -0.32, rl + 0.12], [leg, -0.6, rl],
           [leg, -1.5, rl], [leg, y_lo + 0.1, rl], [leg + 0.2, y_lo - 0.1, rl - 0.05]]
    k_bight = len(pts) - 1
    n_turns = int((y_hi - y_lo) / (2 * r + 0.035))
    turns = coil_y(0, 0, rl, 0.5 * P, 0.5 * P + 2 * P * n_turns, y_lo, y_hi, n=40 * n_turns,
                   rho_fn=lambda a, t: rl + bump(((a + P) % (2 * P)) - P, 0.0, 0.75, rt - rl))
    pts += turns
    k_turns = len(pts) - 1
    # through the bight: under its lifted top, and out beyond the rope end
    pts += [[0.25, y_hi + 0.15, rl + 0.05], [0.04, -0.42, rl + 0.02], [0.0, -0.22, rl - 0.0], [0.0, 0.05, rl - 0.05],
            [0.05, 0.35, rl + 0.15], [0.1, 0.8, rl + 0.3]]
    pts = _dedupe(pts)
    return {'ropes': [{'color': 'c', 'pts': pts}], 'code': None, 'r': r, 'relax': 'repel', 'wrapped': True,
            'objects': [{'type': 'pole', 'axis': 'y', 'c': [0, -2.1, 0], 'radius': ROPE_R, 'len': 4.2, 'rope': True}],
            'marks': {'bight': (0, k_bight), 'turns': (0, k_turns), 'end': (0, len(pts) - 1)}, 'view': {'elev': 8}}


def seizing():
    """Flat seizing: turns of twine round two ropes lying side by side, then two
    frapping turns between them to draw the turns tight."""
    r = TW
    xs = ROPE_R + r + 0.03                      # rope centres (gap between them for the frapping turns)
    rho = ROPE_R + r + 0.01
    y0, n_turns, pitch = -1.0, 9, 2 * r + 0.035
    start = [[0.0, y0 - 1.6, 0.28], [0.0, y0 - 0.9, 0.24], [0.0, y0 + 0.4, 0.2], [0.0, y0 + 1.2, 0.2],
             [0.1, y0 + 1.42, 0.3], [-0.2, y0 + 1.5, rho + 0.1]]
    # the start end is laid in the groove between the ropes and the turns go over it, working down
    turns = _racetrack(xs, rho, y0 + 1.25, n_turns, -pitch, u0=0.95, m_per=44)
    ybot = turns[-1][1]
    ytop = y0 + 1.25
    zf = rho + 2 * r + 0.07
    frap = [[0.0, ybot - 0.2, zf * 0.7]]
    for j in range(2):
        e = j * (2 * r + 0.04)
        frap += [[0.0, ybot - 0.18 - e, zf + e], [0.0, ytop + 0.18 + e, zf + e], [0.0, ytop + 0.24 + e, 0.0],
                 [0.0, ytop + 0.18 + e, -zf - e], [0.0, ybot - 0.18 - e, -zf - e], [0.0, ybot - 0.24 - e, 0.0]]
    end = [[0.0, ybot - 0.45, zf + 0.15], [0.3, ybot - 0.9, zf + 0.2], [0.5, ybot - 1.5, zf + 0.15]]
    pts = _dedupe(start + turns + frap + end)
    k_turns = len(start) + len(turns) - 1
    k_frap = k_turns + len(frap)
    objs = [{'type': 'pole', 'axis': 'y', 'c': [-xs, -0.6, 0], 'radius': ROPE_R, 'len': 5.0, 'rope': True},
            {'type': 'pole', 'axis': 'y', 'c': [xs, -0.6, 0], 'radius': ROPE_R, 'len': 5.0, 'rope': True}]
    return {'ropes': [{'color': 'c', 'pts': pts}], 'code': None, 'r': r, 'relax': 'repel', 'wrapped': True,
            'objects': objs, 'marks': {'start': (0, len(start) - 1), 'turns': (0, k_turns), 'frap': (0, k_frap),
                                       'end': (0, len(pts) - 1)}, 'view': {'elev': 8}}


# ------------------------------------------------------------------ backlog

def marlinspike_hitch():
    """A loop laid over the line with a spike through it: over the loop, under the
    line, over the loop. Holds while there is tension; falls out when the spike is drawn."""
    zl = -0.12                                          # loop edges behind the spike
    zm = 0.42                                           # the line in front of it
    pts = [[0.0, 3.4, 0.0], [0.0, 2.2, 0.0], [0.0, 1.05, 0.05], [-0.08, 0.72, 0.12],
           [-0.62, 0.45, zl], [-0.78, 0.0, zl], [-0.62, -0.48, zl], [0.0, -0.66, zl], [0.62, -0.48, zl], [0.78, 0.0, zl],
           [0.62, 0.45, zl], [0.25, 0.68, 0.0], [0.05, 0.55, zm * 0.7], [0.0, 0.25, zm], [0.0, -0.3, zm],
           [0.0, -0.75, zm * 0.5], [0.0, -1.3, 0.05], [0.0, -2.4, 0.0], [0.0, -3.4, 0.0]]
    pts = [[p[0] * 1.45, p[1] * 1.3 if abs(p[1]) < 1.0 else p[1], p[2]] for p in pts]
    spike = {'type': 'pole', 'axis': 'x', 'c': [0.35, 0.0, 0.14], 'radius': 0.09, 'len': 3.8, 'metal': True}
    return {'ropes': [{'color': 'b', 'pts': pts}], 'code': None, 'objects': [spike], 'closure': [(0, 1)],
            'marks': {'down': (0, 3), 'loop': (0, 12), 'end': (0, len(pts) - 1)}}


def mirrored_rolling_hitch():
    """The rolling hitch made the other way round, for a pull from the opposite side."""
    g = rolling_hitch()
    g['ropes'][0]['pts'] = [[-p[0], p[1], p[2]] for p in g['ropes'][0]['pts']]
    for ob in g['objects']:
        ob['c'] = [-ob['c'][0], ob['c'][1], ob['c'][2]]
    g['ropes'][0]['color'] = 'b'
    return g


def pedigree_cow_hitch():
    """A cow hitch with the loaded leg's partner tucked back up under the bight."""
    g = cow_hitch()
    pts = g['ropes'][0]['pts']
    # pts are in the rotated frame (rail along x, legs hang down at x = +-yl). Replace the
    # last leg's hanging part with a tuck: up under the bight and down in front.
    k = len(pts) - 1
    while k > 0 and pts[k][1] < -0.75:
        k -= 1
    leg_x = pts[-1][0]
    tuck = [[leg_x, -1.15, 0.0], [leg_x * 0.4, -1.5, 0.12], [0.0, -1.2, 0.3], [-0.02, -0.75, 0.32],
            [0.0, -0.3, 0.28], [0.05, -0.05, 0.62], [0.08, -0.5, 0.95], [0.1, -1.4, 0.95], [0.12, -2.4, 0.85]]
    g['ropes'][0]['pts'] = _dedupe(pts[:k + 1] + tuck)
    g['marks']['end'] = (0, len(g['ropes'][0]['pts']) - 1)
    g['ropes'][0]['color'] = 'c'
    return g


def cow_hitch_toggle():
    """Cow hitch through a ring, held by a toggle instead of the ends: pull the
    toggle and it falls apart."""
    ring = {'type': 'ring', 'c': [0.0, 1.35, 0.0], 'radius': 0.62, 'tube': 0.08}
    yb = 1.35 - 0.62                                 # bottom bar of the ring
    zt, yt = 0.95, 0.15                              # toggle in front, below the ring
    toggle = {'type': 'pole', 'axis': 'x', 'c': [0.0, yt, zt], 'radius': 0.1, 'len': 2.4}
    over = yb + 0.08 + R + 0.14
    def leg(x, xb):
        return [[x, -3.2, 0.22], [x, -1.0, 0.22], [x, yb - 0.35, 0.3], [x, over - 0.08, 0.2], [x, over, 0.0],
                [x, over - 0.08, -0.22], [x * 1.3, yb - 0.3, -0.33], [xb, yb - 0.7, -0.32]]
    L1 = leg(-0.17, -0.42)
    L2 = leg(0.17, 0.42)[::-1]
    # bight: from behind, forward outside the front legs, up in front, over the toggle, apex behind it
    def side(xb, xf):
        return [[xb, -0.2, -0.22], [xb * 1.1, -0.42, 0.1], [xf, -0.3, 0.55], [xf, yt - 0.25, zt + 0.25], [xf, yt + 0.12, zt + 0.22],
                [xf, yt + 0.25, zt - 0.05], [xf * 0.8, yt + 0.05, zt - 0.27]]
    s1 = side(-0.42, -0.3)
    s2 = side(0.42, 0.3)[::-1]
    apex = [[0.0, yt - 0.12, zt - 0.32]]
    k = 1.7
    pts = _dedupe([[p[0] * k, p[1] * k, p[2] * k] for p in L1 + s1 + apex + s2 + L2])
    for ob in (ring, toggle):
        ob['c'] = [c * k for c in ob['c']]
    ring['radius'] *= k
    toggle['len'] *= k
    return {'ropes': [{'color': 'c', 'pts': pts}], 'code': None, 'objects': [ring, toggle], 'relax': 'repel', 'wrapped': True,
            'marks': {'up': (0, len(L1) - 1), 'bight': (0, len(L1) + len(s1)), 'end': (0, len(pts) - 1)}}


def bowline_with_stopper():
    """A bowline whose tail is tied in an overhand knot round the leg of the eye beside it."""
    import numpy as np
    g = bowline()
    P = _dense_with_z(g)[0]
    cut = len(P) - 1
    while cut > 0 and P[cut, 1] < -1.75:
        cut -= 1
    head = P[:cut:2].tolist()
    yk = -2.55
    # the right-hand leg of the eye, near height yk
    seg = [p for p in P[: int(len(P) * 0.6)] if abs(p[1] - yk) < 0.25 and p[0] > 0.8]
    lx = float(np.mean([p[0] for p in seg])) if seg else 1.7
    rho = 2 * R + 0.06
    knot = [[head[-1][0] + 0.15, -2.0, 0.05], [lx - rho - 0.05, yk + 0.25, 0.12]]
    n = 22
    for k in range(n + 1):
        t = k / n
        a = math.pi + 2 * math.pi * t
        knot.append([lx + rho * math.cos(a), yk - 0.36 * t, rho * math.sin(a)])
    knot += [[lx - rho * 0.6, yk - 0.5, -0.2], [lx - 0.05, yk - 0.22, -0.34], [lx + 0.34, yk + 0.02, -0.05],
             [lx + 0.44, yk - 0.4, 0.15], [lx + 0.47, yk - 0.9, 0.15]]
    pts = _dedupe(head + knot)
    marks = dict(g['marks'])
    marks['down'] = (0, len(head) - 1)
    marks['stop'] = (0, len(pts) - 1)
    for key in ('stand', 'loop', 'eye', 'up', 'round'):
        i = g['marks'][key][1]
        from knotlib import ctrl_arc_positions
        cs = ctrl_arc_positions(g['ropes'][0]['pts'])
        f = cs[i] / cs[-1]
        marks[key] = (0, int(f * (len(P) - 1) / 2))
    return {'ropes': [{'color': 'a', 'pts': pts}], 'code': None, 'objects': [], 'marks': marks}


def _two_bights_twisted(code, twist_yellow=True, twist_blue=False, k=1.6, raw=False):
    """Square-knot bights with an extra full twist in one or both pairs of legs
    (the surgeon's knot family). Same orientation conventions as _two_bights."""
    from knotlib import ctrl_arc_positions
    red = [[-2.9, 0.19], [-2.55, 0.19], [-2.2, -0.19], [-1.85, 0.19], [-1.4, 0.19]] if twist_yellow else \
          [[-2.9, 0.19], [-2.2, 0.19], [-1.4, 0.19]]
    red += [[-0.85, 0.3], [-0.45, 0.72], [0.0, 0.86], [0.7, 0.86], [1.25, 0.66], [1.56, 0.0], [1.25, -0.66], [0.7, -0.86],
            [0.0, -0.86], [-0.45, -0.72], [-0.85, -0.3], [-1.4, -0.19]]
    red += ([[-1.85, -0.19], [-2.2, 0.19], [-2.55, -0.19], [-3.0, -0.19], [-4.6, -0.19]] if twist_yellow else
            [[-2.6, -0.19], [-4.6, -0.19]])
    blue = [[2.6, 0.5]] + ([[2.3, 0.5], [2.0, 0.5], [1.75, 0.5]] if False else [])
    if twist_blue:
        blue = [[3.3, 0.5], [2.95, 0.5], [2.6, -0.5], [2.25, 0.5], [1.9, 0.5]]
    blue += [[0.6, 0.5], [-0.6, 0.5], [-1.4, 0.5], [-1.8, 0.31], [-1.92, 0.0], [-1.8, -0.31], [-1.4, -0.5], [-0.6, -0.5],
             [0.6, -0.5]]
    blue += ([[1.9, -0.5], [2.25, -0.5], [2.6, 0.5], [2.95, -0.5], [3.4, -0.5], [4.6, -0.5]] if twist_blue else
             [[2.6, -0.5], [4.6, -0.5]])
    red, blue = _scale(red, k, 2.5 * k), _scale(blue, k, 2.5 * k)
    g0 = {'ropes': [{'color': 'a', 'pts': red}, {'color': 'b', 'pts': blue}], 'code': code}
    return g0


def _sheet_bend_3d(turns=1):
    """Sheet bend built in 3D: the blue end comes up through the yellow bight, takes
    `turns` turns round the bight's neck (behind both legs first), then tucks under
    its own standing part."""
    P = math.pi
    ly = 0.38
    red = [[-4.4, -ly, 0], [-2.8, -ly, 0], [-1.4, -ly, 0], [0.0, -ly, 0], [0.6, -ly, 0], [0.92, -0.27, 0], [1.03, 0.0, 0],
           [0.92, 0.27, 0], [0.6, ly, 0], [0.0, ly, 0], [-1.4, ly, 0], [-2.6, ly, 0]]
    rho = ly + R + R + 0.04
    pitch = 2 * R + 0.06
    xb = 0.22
    blue = [[xb, -4.2, -0.05], [xb, -2.0, -0.08], [xb, -0.9, -0.15], [xb, -ly, -0.32], [xb, 0.0, 0.0], [xb - 0.02, ly, 0.32],
            [xb - 0.12, ly + 0.28, 0.32]]
    k_up = len(blue) - 1
    a0, a1 = 0.5 * P, 2 * P * turns
    x0 = -0.3
    x1 = x0 - pitch * turns
    blue += coil_x(0.0, 0.0, rho, a0, a1, x0, x1, n=30 * turns)
    k_round = len(blue) - 1
    # tuck: dive between the legs and under the blue standing part, ending inside the bight
    blue += [[x1 + 0.3, 0.02, rho - 0.2], [-0.25, 0.0, -0.05], [xb, 0.02, -0.38], [0.5, 0.03, -0.25], [0.72, 0.03, -0.05]]
    return {'ropes': [{'color': 'a', 'pts': red}, {'color': 'b', 'pts': _dedupe(blue)}], 'code': None, 'objects': [],
            'closure': [(0, 1), (1, -1)],
            'marks': {'red': (0, len(red) - 1), 'b_up': (1, k_up), 'b_round': (1, k_round), 'b_tuck': (1, len(_dedupe(blue)) - 1)}}


def double_sheet_bend():
    return _sheet_bend_3d(2)


def _sheepshank_2d(k=1.0):
    """Path of a sheepshank: left standing part, half hitch round the left bight,
    bottom strand, right bight, middle strand, left bight, top strand, half hitch
    (point-symmetric copy) round the right bight, right standing part."""
    A = [[-5.6, -0.1], [-4.0, -0.1], [-3.0, -0.12], [-2.4, -0.25], [-1.7, -0.32], [-1.15, -0.05], [-1.05, 0.35],
         [-1.25, 0.82], [-1.7, 1.0], [-2.15, 0.85], [-2.35, 0.35], [-2.25, -0.08], [-2.0, -0.45], [-1.5, -0.7]]
    mid = [[0.0, -0.7], [1.6, -0.7], [2.55, -0.7], [2.95, -0.5], [3.05, -0.2], [2.85, 0.02], [2.4, 0.06], [1.0, 0.03],
           [0.0, 0.0], [-1.0, -0.03], [-2.4, -0.06], [-2.85, -0.02], [-3.05, 0.2], [-2.95, 0.5], [-2.55, 0.7], [-1.6, 0.7], [0.0, 0.7]]
    B = [[-p[0], -p[1]] for p in A][::-1]
    pts = A + mid + B
    return [[p[0] * k, p[1] * k] for p in pts], len(A)


def sheepshank():
    """Shortens a rope: a Z-fold held at each end by a half hitch made in the standing part."""
    import numpy as np
    from knotlib import catmull_rom, resample, find_crossings, z_profile, LIFT
    K = 1.7
    ctrl, nA = _sheepshank_2d(K)
    P, _ = resample(catmull_rom(ctrl), 0.03)
    cr = find_crossings([P])
    n = len(P)
    # which samples belong to each half-hitch loop (first and last 'nA' control points)
    from knotlib import ctrl_arc_positions
    cs = ctrl_arc_positions(ctrl)
    tot = cs[-1]
    a_end = int(cs[nA - 1] / tot * (n - 1))
    b_start = int(cs[len(ctrl) - nA] / tot * (n - 1))
    targets = []
    for c in cr:
        ia, ib = sorted([c['ia'], c['ib']])
        x, y = c['xy']
        in_a = ia <= a_end and ib <= a_end
        in_b = ia >= b_start and ib >= b_start
        if in_a or in_b:                          # the half hitch's own crossing: the end of the loop goes over
            targets += [(ia, -LIFT), (ib, LIFT)]
            continue
        loop_i = ia if ia <= a_end else ib if ib >= b_start else None
        strand_i = ib if loop_i == ia else ia
        cx = -1.7 * K if x < 0 else 1.7 * K
        outer = (x > cx) if x < 0 else (x < cx)    # loop over the strands on the side away from the bight tip
        targets += [(loop_i, LIFT if outer else -LIFT), (strand_i, -LIFT if outer else LIFT)]
    P[:, 2] = z_profile(n, targets)
    pts = P[::2].tolist() + [P[-1].tolist()]
    return {'ropes': [{'color': 'a', 'pts': pts}], 'code': None, 'objects': [], 'closure': [(0, 1)],
            'fractions': {'zfold': 0.0}, 'marks': {'end': (0, len(pts) - 1)}, 'ncross': len(cr)}


def _band_coil(cx, cz, rho, turns, y0, y1, a0, gap):
    """Two parallel strands (a doubled sling) wound together round a vertical axis."""
    s1, s2 = [], []
    n = 36 * turns
    for k in range(n + 1):
        t = k / n
        a = a0 + 2 * math.pi * turns * t
        y = y0 + (y1 - y0) * t
        p = [cx + rho * math.sin(a), y, cz + rho * math.cos(a)]
        s1.append(p)
        s2.append([p[0], y + gap, p[2]])
    return s1, s2


def klemheist():
    """A loop of cord wound round the main rope, working up; the lower end is passed
    through the upper bight and pulled down."""
    rho = 2 * R + 0.03
    gap = 2 * R + 0.04
    turns = 4
    pitch = 2 * gap + 0.04
    y0 = -1.6
    y1 = y0 + pitch * turns
    s1, s2 = _band_coil(0, 0, rho, turns, y0, y1, 0.0, gap)
    zf = rho + 2 * R + 0.06                           # legs, in front of the wraps
    zu = zf + 2 * R + 0.06                            # the top bight, in front of the legs
    top = s2[-1][1]
    # top bight: from the top of the wraps forward and down in front, apex at mid height
    ub = [[0.2, top + 0.05, zu * 0.7], [0.5, top - 0.3, zu], [0.5, (top + y0) / 2 + 0.05, zu],
          [0.3, (top + y0) / 2 - 0.3, zu], [0.0, (top + y0) / 2 - 0.4, zu], [-0.3, (top + y0) / 2 - 0.3, zu], [-0.5, (top + y0) / 2 + 0.05, zu], [-0.5, top - 0.3, zu],
          [-0.2, top + 0.05, zu * 0.7]]
    # legs: from the bottom of the wraps, up in front of the wraps (behind the bight), over its apex, down
    ya = (top + y0) / 2 - 0.15
    def leg(s, x):
        return [[x, y0 - 0.25, rho + 0.1], [x, y0, zf], [x, ya - 0.3, zf], [x, ya + 0.32, zf], [x * 1.2, ya + 0.45, zu + 0.25],
                [x * 1.4, ya + 0.1, zu + 0.45], [x * 1.6, ya - 0.8, zu + 0.45], [x * 1.8, -4.0, zu + 0.3]]
    L1 = leg(s1, 0.17)
    L2 = leg(s2, -0.17)
    # one closed loop: leg L1 up -> wrap strand 1 up -> bight -> wrap strand 2 down -> leg L2 -> far bottom
    sling = L1[::-1][:-1] + [s1[0]]
    sling = list(reversed(L1)) + s1[1:] + ub + list(reversed(s2))[1:] + L2[1:] + [[0.0, -4.25, zu + 0.3]]
    sling = _dedupe(sling)
    main = [[0, -4.2, 0], [0, -2.0, 0], [0, 0, 0], [0, 2.0, 0], [0, 3.2, 0]]
    return {'ropes': [{'color': 'b', 'pts': main}, {'color': 'a', 'pts': sling, 'closed': True}], 'code': None, 'objects': [],
            'relax': 'repel', 'wrapped': True,
            'marks': {'main': (0, len(main) - 1), 'legs': (1, len(L1)), 'wraps': (1, len(L1) + len(s1) - 1),
                      'bight': (1, len(L1) + len(s1) + len(ub)), 'all': (1, len(sling) - 1)}}


def italian_hitch():
    """Munter hitch on a bar: like a cow hitch, but the crossing part goes over one
    leg and under the other, so both strands leave on the same side and the rope
    can run round the bar under control."""
    rho = POLE * 0.5 + R + 0.015
    pr = POLE * 0.5
    yl = 0.27
    pitch = 2 * R + 0.06
    up = coil_y(0, 0, rho, 0.5 * math.pi, 2.5 * math.pi, yl + 0.04, yl + 0.04 + pitch, n=30)
    top = up[-1][1]
    zb = 2 * R + 0.07
    xb = rho + 0.35
    bridge = [[rho + 0.15, top + 0.02, 0.15], [xb, top * 0.7, zb], [xb, yl, zb], [xb, 0.0, 0.0],
              [xb, -yl, -zb], [xb, -top * 0.7, -zb], [rho + 0.15, -top - 0.02, -0.15]]
    down = coil_y(0, 0, rho, 2.5 * math.pi, 0.5 * math.pi, -top, -(yl + 0.04), n=30)
    legs_x = 3.4
    leg1 = [[legs_x, yl, 0], [legs_x - 1.2, yl, 0], [rho + 0.7, yl, 0], [rho + 0.15, yl + 0.02, 0]]
    leg2 = [[rho + 0.15, -yl - 0.02, 0], [rho + 0.7, -yl, 0], [legs_x - 1.2, -yl, 0], [legs_x, -yl, 0]]
    pts = _dedupe(leg1 + up[1:] + bridge + down + leg2)
    pts = [[p[1], -p[0], p[2]] for p in pts]
    return {'ropes': [{'color': 'a', 'pts': pts}], 'code': None,
            'objects': [{'type': 'pole', 'axis': 'x', 'c': [0, 0, 0], 'radius': pr, 'len': 2.6, 'metal': True}],
            'marks': {'load': (0, len(leg1) - 1), 'over': (0, len(leg1) + len(up) - 2),
                      'cross': (0, len(leg1) + len(up) + len(bridge) - 2), 'end': (0, len(pts) - 1)}}


def bachmann_knot():
    """NOT PUBLISHED: the wraps still pass through the carabiner spine and tangle
    after relaxation. A loop of cord clipped into a carabiner and wound round the rope and the
    carabiner's spine together. Hold the carabiner to slide it; load the cord to grip."""
    rc = 0.2
    xs = 0.48                                         # carabiner spine beside the main rope
    sp = 0.07
    cx = xs / 2
    rho = R + R + 0.04                                # racetrack round rope and spine
    gap = 2 * R + 0.04
    turns = 3
    pitch = 2 * gap + 0.05
    y1 = 0.9
    y0 = y1 - pitch * turns
    s1 = _racetrack(xs / 2, rho, y1, turns, -pitch, u0=0.0, m_per=40)
    s1 = [[p[0] + cx, p[1], p[2]] for p in s1]
    s2 = [[p[0], p[1] + gap, p[2]] for p in s1]
    ytop = s2[0][1]
    # the top bight goes round the far side of the carabiner (clipped in)
    fx = xs + 1.2
    clip = [[cx + 0.25, ytop + 0.12, rho * 0.6], [1.0, ytop + 0.12, 0.3], [fx - 0.05, ytop + 0.08, 0.26], [fx + 0.27, ytop + 0.02, 0.0],
            [fx - 0.05, ytop - 0.04, -0.26], [1.0, ytop - 0.08, -0.3], [cx + 0.25, ytop - 0.1, -rho * 0.6]]
    legs = 3.6
    def leg(s, dz):
        p = s[-1]
        return [[p[0] + 0.1, p[1] - 0.25, p[2] * 0.5 + dz + 0.25], [0.5, p[1] - 1.0, 0.5 + dz], [1.1, -legs - 0.6, 0.5 + dz]]
    L1 = leg(s1, 0.17)
    L2 = leg(s2, -0.17)
    sling = _dedupe(list(reversed(s1)) + clip + s2 + L2 + [[1.15, -legs - 0.25, 0.3]] + list(reversed(L1)))
    main = [[0, -4.0, 0], [0, -2.0, 0], [0, 0, 0], [0, 2.0, 0], [0, 3.0, 0]]
    main = [[p[0] - 0.0, p[1], p[2]] for p in main]
    yt, yb = ytop + 0.7, y0 - 0.75
    objs = [{'type': 'pole', 'axis': 'y', 'c': [xs, (yt + yb) / 2, 0], 'radius': sp, 'len': yt - yb, 'metal': True},
            {'type': 'pole', 'axis': 'y', 'c': [xs + 1.2, (yt + yb) / 2, 0], 'radius': sp, 'len': yt - yb, 'metal': True},
            {'type': 'arc', 'c': [xs + 0.6, yt, 0], 'radius': 0.6, 'tube': sp, 'a0': 0.0, 'a1': math.pi},
            {'type': 'arc', 'c': [xs + 0.6, yb, 0], 'radius': 0.6, 'tube': sp, 'a0': math.pi, 'a1': 2 * math.pi}]
    return {'ropes': [{'color': 'b', 'pts': [[p[0] - rc * 0, p[1], p[2]] for p in main]}, {'color': 'a', 'pts': sling, 'closed': True}],
            'code': None, 'objects': objs, 'relax': 'repel', 'wrapped': True,
            'marks': {'main': (0, len(main) - 1), 'all': (1, len(sling) - 1)}}


def _tube_weave(n_each, pattern, rc, pitch, y0, y1, r_ann=8.0, lift=0.17):
    """Tubular braid: n_each strands spiral one way and n_each the other way round a
    cylinder of radius rc, woven `pattern` over / `pattern` under (1 = plain, 2 = twill).
    Built on the annulus picture of the cylinder, then rolled up."""
    import numpy as np
    from knotlib import find_crossings, z_profile
    ys = np.arange(y0, y1 + 1e-9, 0.03)
    parts = []
    for fam, sgn in ((0, 1), (1, -1)):
        for i in range(n_each):
            th = 2 * math.pi * (i + 0.5 * fam) / n_each + sgn * 2 * math.pi * (ys - y0) / pitch
            parts.append({'theta': th, 'y': ys, 'fam': fam})
    ann = [np.column_stack([(r_ann + p['y']) * np.cos(p['theta']), (r_ann + p['y']) * np.sin(p['theta']), np.zeros(len(ys))])
           for p in parts]
    cr = find_crossings(ann)
    passes = {k: [] for k in range(len(parts))}
    for ci, c in enumerate(cr):
        a = c['ra'] if parts[c['ra']]['fam'] == 0 else c['rb']
        fa = c['ia'] if a == c['ra'] else c['ib']
        passes[a].append((fa, ci))
    tg = [[] for _ in parts]
    for k, lst in passes.items():
        lst.sort()
        off = k % 2 if pattern == 1 else k % 4 // 1
        for n_, (f, ci) in enumerate(lst):
            c = cr[ci]
            over = ((n_ + off) // pattern) % 2 == 0
            b = c['rb'] if c['ra'] == k else c['ra']
            fb = c['ib'] if c['ra'] == k else c['ia']
            tg[k].append((f, lift if over else -lift))
            tg[b].append((fb, -lift if over else lift))
    out = []
    for k, p in enumerate(parts):
        off = z_profile(len(ys), tg[k], plateau=0.9 * R / 0.03, ramp=2.2 * R / 0.03)
        rho = rc + off
        out.append(np.column_stack([rho * np.sin(p['theta']), ys, rho * np.cos(p['theta'])]))
    return out, len(cr)


def _sennit(n_each, pattern, rc, pitch, colors):
    P3, ncross = _tube_weave(n_each, pattern, rc, pitch, -2.6, 2.6)
    ropes = []
    for k, P in enumerate(P3):
        top, bot = P[-1], P[0]
        dy = 0.6 if k >= len(P3) // 2 else 0.0
        ends = [[top[0] * 2.0, top[1] + 0.55 + dy, top[2] * 2.0], [top[0] * 3.2, top[1] + 1.3 + dy, top[2] * 3.2]]
        starts = [[bot[0] * 3.2, bot[1] - 1.3, bot[2] * 3.2], [bot[0] * 2.0, bot[1] - 0.55, bot[2] * 2.0]]
        ropes.append({'color': colors[k % len(colors)], 'pts': starts + P[::3].tolist() + ends})
    fl = {'a': [0.33] * len(ropes), 'b': [0.66] * len(ropes)}
    return {'ropes': ropes, 'code': None, 'objects': [], 'relax': 'repel', 'wrapped': True, 'ncross': ncross,
            'fraction_lists': fl, 'marks': {'end': (0, len(ropes[0]['pts']) - 1)}, 'view': {'elev': 12}}


def round_sennit_4():
    return _sennit(2, 1, 0.3, 2.2, ['a', 'b', 'c', 'a'])


def square_sennit_8():
    return _sennit(4, 2, 0.52, 3.0, ['a', 'b', 'c', 'b'])


def _surgeon_layout(tw_bottom=0, tw_top=0):
    """Square-knot bights with an extra full twist between the two standing parts
    (surgeon's first half) and, for the second tuck, between the two working ends."""
    red=[[-2.9,0.19],[-2.2,0.19],[-1.4,0.19],[-0.85,0.3],[-0.45,0.72],[0.0,0.86],[0.7,0.86],[1.25,0.66],[1.56,0.0],[1.25,-0.66],[0.7,-0.86],[0.0,-0.86],[-0.45,-0.72],[-0.85,-0.3],[-1.4,-0.19],[-2.6,-0.19],[-4.6,-0.19]]
    blue=[[2.6,0.5],[0.6,0.5],[-0.6,0.5],[-1.4,0.5],[-1.8,0.31],[-1.92,0.0],[-1.8,-0.31],[-1.4,-0.5],[-0.6,-0.5],[0.6,-0.5],[2.6,-0.5],[4.6,-0.5]]
    if tw_bottom:
        red=red[:10]+[[0.9,-0.86],[0.6,-0.5],[0.3,-0.86],[0.0,-0.5],[-0.3,-0.86]]+red[12:]
        blue=blue[:8]+[[-0.3,-0.5],[0.0,-0.86],[0.3,-0.5],[0.6,-0.86],[0.9,-0.5]]+blue[10:]
    if tw_top:
        red=red[:5]+[[-0.3,0.86],[0.0,0.5],[0.3,0.86],[0.6,0.5],[0.9,0.86]]+red[7:]
        blue=blue[:1]+[[0.9,0.5],[0.6,0.86],[0.3,0.5],[0.0,0.86],[-0.3,0.5]]+blue[3:]
    red=_scale(red,1.7,99); blue=_scale(blue,1.7,99)
    return red,blue


def _surgeon(code, tw_top=0):
    red, blue = _surgeon_layout(1, tw_top)
    g0 = {'ropes': [{'color': 'a', 'pts': red}, {'color': 'b', 'pts': blue}], 'code': code}
    Ps = [P[::-1].copy() for P in _dense_with_z(g0)]
    return {'ropes': [{'color': 'a', 'pts': Ps[0][::2].tolist() + [Ps[0][-1].tolist()]},
                      {'color': 'b', 'pts': Ps[1][::2].tolist() + [Ps[1][-1].tolist()]}],
            'code': None, 'objects': [], 'closure': [(0, 1), (1, -1)],
            'rope_fractions': {'in': (1, 0.42), 'bend': (1, 0.6)}, 'marks': {'red': (0, len(Ps[0][::2])), 'blue': (1, len(Ps[1][::2]))}}


SURGEON_CODE = 'uouuuuouou'


def surgeons_knot():
    return _surgeon(SURGEON_CODE)


def surgeons_knot_second_tuck():
    return _surgeon('uouooouuuuouou', tw_top=1)


def highwaymans_hitch():
    """Draw hitch on a rail: a bight of the working part over the rail; a bight of the
    standing part up through it; a bight of the end through that. Load the standing
    part; pull the end and the whole thing falls off the rail."""
    pr = 0.25
    zr = pr + R + 0.04                      # just clear of the rail
    x2, x1, x3 = 0.4, 0.75, 0.15            # half-widths: standing bight, working bight, end bight
    z2, z1, z3 = zr + 0.2, zr + 0.55, zr + 0.9
    top = pr + R + 0.05
    pts = [[-x2, -4.0, z2], [-x2, -2.0, z2], [-x2, -0.7, z2],
           # second bight (standing part) up through the first, apex above the rail in front
           [-x2, top + 0.2, z2 - 0.05], [-x2 * 0.6, top + 0.62, z2 - 0.15], [0.0, top + 0.72, z2 - 0.18],
           [x2 * 0.6, top + 0.62, z2 - 0.15], [x2, top + 0.2, z2 - 0.05], [x2, -0.7, z2], [x2, -1.25, z2 - 0.05],
           # round underneath and up behind the rail: the first bight (working part)
           [x1 * 0.8, -1.6, 0.05], [x1, -1.3, -zr], [x1, -0.25, -zr], [x1, 0.3, -zr * 0.78], [x1, top + 0.05, 0.0],
           [x1, 0.15, z1 * 0.7], [x1, -0.55, z1], [x1 * 0.6, -0.95, z1], [0.0, -1.05, z1], [-x1 * 0.6, -0.95, z1],
           [-x1, -0.55, z1], [-x1, 0.15, z1 * 0.7], [-x1, top + 0.05, 0.0], [-x1, 0.3, -zr * 0.78], [-x1, -0.25, -zr],
           [-x1, -1.3, -zr], [-x1 * 1.05, -1.75, 0.3], [-0.6, -1.95, 1.05],
           # the end: a bight up in front and through the second bight, apex behind it
           [-x3, -1.6, z3], [-x3, -0.4, z3], [-x3, top + 0.3, z3 * 0.7], [-x3, top + 0.5, 0.15], [0.0, top + 0.45, -0.08],
           [x3, top + 0.5, 0.15], [x3, top + 0.3, z3 * 0.7], [x3, -0.4, z3], [x3, -1.2, z3], [x3 + 0.05, -1.8, z3]]
    pts = _dedupe(pts)
    return {'ropes': [{'color': 'b', 'pts': pts}], 'code': None, 'closure': [(0, 1)],
            'objects': [{'type': 'pole', 'axis': 'x', 'c': [0, 0, 0], 'radius': pr, 'len': 3.4}],
            'marks': {'first': (0, 26), 'second': (0, 9), 'end': (0, len(pts) - 1)}, 'view': {'elev': 10}}


def palomar_knot():
    """A bight of line through the eye of the hook, an overhand knot tied with the
    doubled line, and the loop of the bight passed over the hook so it lassos the shank."""
    import numpy as np
    base = [[-3.6, 0.0], [-2.2, 0.0], [-1.0, 0.0], [0.0, 0.02], [0.55, 0.27], [0.82, 0.75], [0.58, 1.22], [0.0, 1.32],
            [-0.5, 1.02], [-0.56, 0.42], [-0.4, -0.3], [-0.05, -0.62], [0.32, -0.45], [0.36, 0.12], [0.4, 0.55],
            [0.95, 0.8], [1.6, 0.78]]
    base = _rot(_scale(base, 1.2, 1.8), 'cw')
    A, _, B = _doubled(base, 'uou', z_gain=1.3)
    # move so the bottom of the doubled line sits just above the eye
    er = 0.46
    ey = 0.5
    end = (A[-1, :2] + B[-1, :2]) / 2
    shift = np.array([-end[0], ey + er + 0.75 - end[1]])
    A[:, :2] += shift
    B[:, :2] += shift
    a0, b0 = A[-1], B[-1]
    xa, xb = a0[0], b0[0]
    rr = SHANK_R + R + 0.04
    yl = -0.5
    def down(p, x):
        return [[x, p[1] - 0.3, 0.32], [x * 0.9, ey + 0.1, 0.36], [x * 0.8, ey, 0.0], [x * 0.9, ey - 0.12, -0.36],
                [x, yl + 0.3, -0.32]]
    da, db = down(a0, xa), down(b0, xb)
    sa = 1 if xa > xb else -1
    lasso = [[sa * rr, yl, -0.12], [sa * rr * 1.1, yl - 0.05, 0.12], [0.0, yl - 0.1, rr + 0.04], [-sa * rr * 1.1, yl - 0.05, 0.12],
             [-sa * rr, yl, -0.12]]
    pts = A[::3].tolist() + da + lasso + db[::-1] + B[::-3].tolist()
    pts = _dedupe(pts)
    n = len(pts)
    hook = _hook()
    hook[0] = {'type': 'ring', 'c': [0.0, ey, 0], 'radius': er, 'tube': EYE_T}
    na = len(A[::3])
    return {'ropes': [{'color': 'a', 'pts': pts}], 'code': None, 'objects': hook, 'relax': 'repel', 'wrapped': True,
            'fraction_lists': {'knot': [0.32], 'eye': [na / n], 'lasso': [(na + len(da) + len(lasso)) / n]},
            'marks': {'end': (0, n - 1)}}


def bimini_twist(twists=8):
    """Long double-line loop: the loop is twisted many times, the end wound back down over
    the twists, then locked with a half hitch round one leg."""
    rt = R + 0.05
    top = 3.2
    pitch_t = 0.68
    y0 = top - pitch_t * twists
    s1, s2 = [], []
    n = 30 * twists
    for k in range(n + 1):
        t = k / n
        a = 2 * math.pi * twists * t
        y = top - (top - y0) * t
        s1.append([rt * math.cos(a), y, rt * math.sin(a)])
        s2.append([-rt * math.cos(a), y, -rt * math.sin(a)])
    # standing line in from above as strand 1; the loop below joins strand 1 to strand 2
    stand = [[s1[0][0], top + 2.2, 0.0], [s1[0][0], top + 1.0, 0.0]]
    loop = [[s1[-1][0] * 1.5, y0 - 0.5, 0.0], [0.9, y0 - 2.0, 0.0], [0.0, y0 - 3.2, 0.0], [-0.9, y0 - 2.0, 0.0],
            [s2[-1][0] * 1.5, y0 - 0.5, 0.0]]
    # end: strand 2 continues at the top and winds back down over the twists
    ro = 2 * rt + 2 * R + 0.06
    n_c = int((top - y0 - 0.4) / (2 * R + 0.14))
    coil = [[s2[0][0] * 1.3, top + 0.5, 0.1], [ro * 0.6, top + 0.45, ro * 0.6]]
    m = 24 * n_c
    for k in range(m + 1):
        t = k / m
        a = 0.5 * math.pi + 2 * math.pi * n_c * t
        coil.append([ro * math.sin(a), top - 0.05 - (top - y0 - 0.45) * t, ro * math.cos(a)])
    lx, ly = 0.47, y0 - 1.0
    lock = [[0.65, y0 - 0.25, 0.5], [lx, ly + 0.25, 0.48], [lx + 0.48, ly + 0.05, 0.0], [lx, ly - 0.1, -0.46],
            [lx - 0.44, ly - 0.2, 0.0], [lx - 0.05, ly - 0.35, 0.48], [lx + 0.55, ly - 0.6, 0.5], [1.6, ly - 1.3, 0.45]]
    pts = _dedupe(stand + s1 + loop + s2[::-1] + coil + lock)
    k1 = len(stand) + len(s1) + len(loop) + len(s2)
    return {'ropes': [{'color': 'b', 'pts': pts}], 'code': None, 'objects': [], 'relax': False, 'wrapped': True,
            'marks': {'twist': (0, k1 - 1), 'coil': (0, k1 + len(coil) - 1), 'end': (0, len(pts) - 1)}, 'view': {'elev': 6}}
