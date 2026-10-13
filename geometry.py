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

def square_knot():
    """Two interlocked bights. Red (left end) bight bends right; blue (right end)
    bight bends left. Each bight's curve lies over the other's legs."""
    red = [[-4.6, 0.19], [-2.6, 0.19], [-1.4, 0.19], [-0.85, 0.3], [-0.45, 0.72], [0.0, 0.86], [0.7, 0.86],
           [1.25, 0.66], [1.56, 0.0], [1.25, -0.66], [0.7, -0.86], [0.0, -0.86], [-0.45, -0.72], [-0.85, -0.3],
           [-1.4, -0.19], [-2.6, -0.19], [-4.6, -0.19]]
    blue = [[4.6, 0.5], [2.6, 0.5], [0.6, 0.5], [-0.6, 0.5], [-1.4, 0.5], [-1.8, 0.31], [-1.92, 0.0], [-1.8, -0.31],
            [-1.4, -0.5], [-0.6, -0.5], [0.6, -0.5], [2.6, -0.5], [4.6, -0.5]]
    red, blue = _scale(red, 1.6, 4.0), _scale(blue, 1.6, 4.0)
    return {'ropes': [{'color': 'a', 'pts': red}, {'color': 'b', 'pts': blue}], 'code': 'uoooou', 'objects': [],
            'marks': {'red': (0, len(red) - 1), 'b_in': (1, 4), 'b_bend': (1, 8), 'b_out': (1, len(blue) - 1)}}


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
