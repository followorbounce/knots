"""Geometry engine for Knot Atlas.

A knot is described by one or more ropes. Each rope is a list of control
points [x, y] or [x, y, z]. The engine:

1. smooths the control points with a centripetal Catmull-Rom spline and
   resamples the result at an even arc-length spacing;
2. optionally resolves over/under from a crossing code ("diagram" knots):
   every crossing in the 2D projection is visited twice while walking the
   ropes in order; the first visit reads the next letter of the code
   ('o' = this strand passes over, 'u' = under) and the strands are lifted
   or lowered around that point;
3. checks the result: no rope may pass through itself, another rope or an
   object, and the number of crossings must match the code;
4. exports the sampled centrelines, crossings and step data for the 3D
   viewer, and draws flat SVG diagrams of every step.

Coordinates: x right, y up, z towards the viewer. Units are arbitrary;
rope radius R is the yardstick.
"""
import math
import numpy as np

R = 0.15            # rope radius
DS = 0.045          # resample spacing
LIFT = 1.12 * R     # how far a strand is lifted/lowered at a crossing

ROPE_COLORS = {
    'a': ('#d39a2c', '#7a4f0c'),   # manila / ochre
    'b': ('#2f7f8a', '#14424a'),   # teal
    'c': ('#b5523a', '#5c2214'),   # rust
}


# ---------------------------------------------------------------- spline

def catmull_rom(ctrl, per_seg=14, alpha=0.5):
    P = np.asarray([p if len(p) == 3 else (p[0], p[1], 0.0) for p in ctrl], float)
    if len(P) < 2:
        return P
    P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]

        def tj(ti, a, b):
            return ti + max(np.linalg.norm(b - a), 1e-6) ** alpha
        t0 = 0.0
        t1 = tj(t0, p0, p1)
        t2 = tj(t1, p1, p2)
        t3 = tj(t2, p2, p3)
        for k in range(per_seg):
            t = t1 + (t2 - t1) * k / per_seg
            a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    out.append(P[-2])
    return np.asarray(out)


def resample(poly, ds=DS):
    seg = np.linalg.norm(np.diff(poly, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(2, int(round(s[-1] / ds)) + 1)
    t = np.linspace(0, s[-1], n)
    out = np.column_stack([np.interp(t, s, poly[:, k]) for k in range(3)])
    return out, t


def ctrl_arc_positions(ctrl, per_seg=14):
    """Arc length at which the spline passes each control point."""
    dense = catmull_rom(ctrl, per_seg)
    seg = np.linalg.norm(np.diff(dense, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    return [float(s[min(i * per_seg, len(s) - 1)]) for i in range(len(ctrl))]


# ---------------------------------------------------------------- crossings

def _seg_intersections(A, B, same, min_gap):
    """All 2D intersections between polyline A and polyline B."""
    res = []
    a0, a1 = A[:-1, :2], A[1:, :2]
    b0, b1 = B[:-1, :2], B[1:, :2]
    amin = np.minimum(a0, a1); amax = np.maximum(a0, a1)
    bmin = np.minimum(b0, b1); bmax = np.maximum(b0, b1)
    for i in range(len(a0)):
        m = (bmin[:, 0] <= amax[i, 0]) & (bmax[:, 0] >= amin[i, 0]) & \
            (bmin[:, 1] <= amax[i, 1]) & (bmax[:, 1] >= amin[i, 1])
        idx = np.nonzero(m)[0]
        if same:
            idx = idx[idx > i + min_gap]
        for j in idx:
            p, q, r_, u = a0[i], a1[i], b0[j], b1[j]
            d = (q[0] - p[0]) * (u[1] - r_[1]) - (q[1] - p[1]) * (u[0] - r_[0])
            if abs(d) < 1e-12:
                continue
            ta = ((r_[0] - p[0]) * (u[1] - r_[1]) - (r_[1] - p[1]) * (u[0] - r_[0])) / d
            tb = ((r_[0] - p[0]) * (q[1] - p[1]) - (r_[1] - p[1]) * (q[0] - p[0])) / d
            if 0 <= ta < 1 and 0 <= tb < 1:
                res.append((i + ta, j + tb))
    return res


def find_crossings(ropes):
    """ropes: list of (N,3) arrays. Returns crossings sorted by nothing."""
    out = []
    for k in range(len(ropes)):
        for l in range(k, len(ropes)):
            for fa, fb in _seg_intersections(ropes[k], ropes[l], k == l, 3):
                out.append({'ra': k, 'ia': fa, 'rb': l, 'ib': fb})
    for c in out:
        A, B = ropes[c['ra']], ropes[c['rb']]
        c['za'] = _interp(A, c['ia'])[2]
        c['zb'] = _interp(B, c['ib'])[2]
        c['xy'] = _interp(A, c['ia'])[:2]
    return out


def _interp(P, f):
    i = int(math.floor(f)); i = max(0, min(len(P) - 2, i)); t = f - i
    return P[i] * (1 - t) + P[i + 1] * t


def apply_code(ropes, code):
    """Lift/lower strands at each crossing according to the code."""
    cr = find_crossings(ropes)
    visits = []
    for ci, c in enumerate(cr):
        visits.append((c['ra'], c['ia'], ci, 'a'))
        visits.append((c['rb'], c['ib'], ci, 'b'))
    visits.sort(key=lambda v: (v[0], v[1]))
    seen = {}
    k = 0
    for rope, f, ci, side in visits:
        if ci in seen:
            continue
        if k >= len(code):
            raise ValueError('code too short: %d crossings, code has %d letters' % (len(cr), len(code)))
        over = code[k] == 'o'
        k += 1
        seen[ci] = (side, over)
    if k != len(code):
        raise ValueError('code length %d but %d crossings found' % (len(code), len(cr)))
    targets = [[] for _ in ropes]
    for ci, c in enumerate(cr):
        side, over = seen[ci]
        a_over = over if side == 'a' else not over
        targets[c['ra']].append((c['ia'], LIFT if a_over else -LIFT))
        targets[c['rb']].append((c['ib'], -LIFT if a_over else LIFT))
    out = []
    for P, tg in zip(ropes, targets):
        P = P.copy()
        P[:, 2] += z_profile(len(P), tg)
        out.append(P)
    return out


def _smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def z_profile(n, targets, plateau=1.25 * R / DS, ramp=3.2 * R / DS):
    """Height along a strand: flat at each crossing's target, eased in between,
    back to zero where crossings are far apart."""
    z = np.zeros(n)
    if not targets:
        return z
    tg = sorted(targets)
    for i in range(n):
        left = [t for t in tg if t[0] <= i]
        right = [t for t in tg if t[0] > i]
        L = left[-1] if left else None
        Rt = right[0] if right else None
        def solo(t):
            d = abs(i - t[0])
            if d <= plateau:
                return t[1]
            return t[1] * _smooth(1 - (d - plateau) / ramp)
        if L and Rt and (Rt[0] - L[0]) <= 2 * (plateau + ramp):
            a, b = L[0] + plateau, Rt[0] - plateau
            if i <= a:
                z[i] = L[1]
            elif i >= b:
                z[i] = Rt[1]
            else:
                w = _smooth((i - a) / max(1e-9, b - a))
                z[i] = L[1] * (1 - w) + Rt[1] * w
        else:
            v = [solo(t) for t in (L, Rt) if t]
            z[i] = max(v, key=abs)
    return z


# ---------------------------------------------------------------- helpers for 3D authoring

def coil_y(cx, cz, rho, a0, a1, y0, y1, n=None, rho_fn=None, ease=1.0, yfn=None):
    """Points on a helix round a vertical axis. a=0 front (+z), a=pi/2 right (+x).
    ease > 1 keeps y near y0 and changes it late in the turn."""
    n = n or max(4, int(abs(a1 - a0) / 0.25) + 1)
    pts = []
    for k in range(n + 1):
        t = k / n
        a = a0 + (a1 - a0) * t
        rr = rho_fn(a, t) if rho_fn else rho
        pts.append([cx + rr * math.sin(a), yfn(a, t) if yfn else y0 + (y1 - y0) * t ** ease, cz + rr * math.cos(a)])
    return pts


def coil_x(cy, cz, rho, a0, a1, x0, x1, n=None, rho_fn=None):
    """Helix round a horizontal (x) axis. a=0 front (+z), a=pi/2 top (+y)."""
    n = n or max(4, int(abs(a1 - a0) / 0.25) + 1)
    pts = []
    for k in range(n + 1):
        t = k / n
        a = a0 + (a1 - a0) * t
        rr = rho_fn(a, t) if rho_fn else rho
        pts.append([x0 + (x1 - x0) * t, cy + rr * math.sin(a), cz + rr * math.cos(a)])
    return pts


def bump(a, centre, half, amount):
    """Smooth raised-cosine bump of width 2*half around centre."""
    d = abs(a - centre)
    if d >= half:
        return 0.0
    return amount * 0.5 * (1 + math.cos(math.pi * d / half))


# ---------------------------------------------------------------- knot build

def build(knot):
    """Sample ropes, resolve z, compute crossings, steps and checks."""
    r = knot.get('r', R)
    ropes, arcs, ctrl_s = [], [], []
    for rope in knot['ropes']:
        dense = catmull_rom(rope['pts'])
        P, s = resample(dense)
        ropes.append(P)
        arcs.append(s)
        ctrl_s.append(ctrl_arc_positions(rope['pts']))
    if knot.get('code') is not None:
        ropes = apply_code(ropes, knot['code'])
    cr = find_crossings(ropes)
    for c in cr:
        c['a_over'] = bool(c['za'] > c['zb'])
        c['gap'] = abs(c['za'] - c['zb'])

    # step visibility: per step, per rope, arc fraction
    steps = []
    vis = [0.0] * len(ropes)
    for st in knot['steps']:
        show = st.get('show', {})
        for k, v in show.items():
            if v == 'all':
                vis[k] = 1.0
            elif isinstance(v, float):
                vis[k] = v
            else:
                vis[k] = ctrl_s[k][v] / arcs[k][-1]
        steps.append(dict(st, vis=list(vis)))

    # which step reveals each sample -> labels at crossings made in that step
    def step_of(rope, f):
        frac = f / (len(ropes[rope]) - 1)
        for i, st in enumerate(steps):
            if st['vis'][rope] >= frac - 1e-6:
                return i
        return len(steps) - 1
    for c in cr:
        ta, tb = step_of(c['ra'], c['ia']), step_of(c['rb'], c['ib'])
        if ta > tb or (ta == tb and (c['ra'], c['ia']) > (c['rb'], c['ib'])):
            c['step'], c['mover_over'] = ta, c['a_over']
        else:
            c['step'], c['mover_over'] = tb, not c['a_over']
        c['top'] = float(max(c['za'], c['zb']) + r)

    # checks
    problems = []
    if knot.get('code') is not None and len(cr) != len(knot['code']):
        problems.append('crossings %d != code %d' % (len(cr), len(knot['code'])))
    for c in cr:
        if c['gap'] < 2 * r * 0.98:
            problems.append('crossing at (%.2f,%.2f) gap %.3f < %.3f' % (c['xy'][0], c['xy'][1], c['gap'], 2 * r))
    worst = min_clearance(ropes, r, [rp.get('closed', False) for rp in knot['ropes']], knot.get('joined', False))
    if worst[0] < 2 * r * 0.93:
        problems.append('rope clearance %.3f < %.3f near %s' % (worst[0], 2 * r, np.round(worst[1], 2).tolist()))
    for ob in knot.get('objects', []):
        d, where = object_clearance(ropes, ob)
        if d < -0.02:
            problems.append('%s overlap %.3f near %s' % (ob['type'], d, np.round(where, 2).tolist()))
    return {'ropes': ropes, 'crossings': cr, 'steps': steps, 'problems': problems, 'r': r}


def min_clearance(ropes, r, closed=None, joined=False):
    """Smallest distance between rope centrelines that are not neighbours along
    the rope. joined=True: the ropes are two halves of one rope meeting at their
    last points, so the meeting point is not a clash."""
    closed = closed or [False] * len(ropes)
    best = (1e9, None)
    skip = int(math.ceil(4 * r / DS))
    for k in range(len(ropes)):
        A = ropes[k][::2]
        for l in range(k, len(ropes)):
            B = ropes[l][::2]
            D = np.linalg.norm(A[:, None, :] - B[None, :, :], axis=2)
            if k == l:
                n = len(A)
                ii, jj = np.indices((n, n))
                gap = np.abs(ii - jj)
                if closed[k]:
                    gap = np.minimum(gap, n - gap)
                D[gap * 2 <= skip] = 1e9
            elif joined:
                ii, jj = np.indices(D.shape)
                D[((len(A) - 1 - ii) + (len(B) - 1 - jj)) * 2 <= skip] = 1e9
            i, j = np.unravel_index(np.argmin(D), D.shape)
            if D[i, j] < best[0]:
                best = (float(D[i, j]), A[i])
    return best


def object_clearance(ropes, ob):
    """Distance from rope surface to object surface (positive = clear)."""
    best = (1e9, None)
    for P in ropes:
        if ob['type'] == 'pole':
            c = np.array(ob['c'], float)
            ax = {'x': 0, 'y': 1, 'z': 2}[ob['axis']]
            Q = P - c
            Q[:, ax] = 0
            d = np.linalg.norm(Q, axis=1) - ob['radius'] - R
            inside = np.abs(P[:, ax] - c[ax]) < ob['len'] / 2
            d = np.where(inside, d, 1e9)
        elif ob['type'] == 'ring':
            c = np.array(ob['c'], float)
            Q = P - c
            rho = np.hypot(Q[:, 0], Q[:, 1])
            d = np.hypot(rho - ob['radius'], Q[:, 2]) - ob['tube'] - R
        else:
            continue
        i = int(np.argmin(d))
        if d[i] < best[0]:
            best = (float(d[i]), P[i])
    return best


# ---------------------------------------------------------------- SVG diagrams

def _chunks(P, size=5):
    n = len(P)
    for i in range(0, n - 1, size):
        yield i, min(n - 1, i + size)


def svg_diagram(knot, built, step_index=None, scale=60, pad=0.6, labels=True, tags_for_step=True):
    """Flat drawing of the knot with correct over/under. step_index=None -> finished knot."""
    r = built['r']
    ropes = built['ropes']
    vis = built['steps'][step_index]['vis'] if step_index is not None else [1.0] * len(ropes)
    allp = np.vstack(ropes)
    xs, ys = allp[:, 0], allp[:, 1]
    for ob in knot.get('objects', []):
        xs = np.concatenate([xs, _obj_extent(ob)[0]])
        ys = np.concatenate([ys, _obj_extent(ob)[1]])
    x0, x1 = xs.min() - r - pad, xs.max() + r + pad
    y0, y1 = ys.min() - r - pad, ys.max() + r + pad
    W, H = (x1 - x0) * scale, (y1 - y0) * scale

    def X(x): return (x - x0) * scale
    def Y(y): return (y1 - y) * scale

    items = []  # (z, svg)
    for ob in knot.get('objects', []):
        items.extend(_obj_svg(ob, X, Y, scale))
    for k, P in enumerate(ropes):
        n = int(round(vis[k] * (len(P) - 1)))
        if n < 1:
            continue
        col, edge = ROPE_COLORS[knot['ropes'][k].get('color', 'a')]
        w_out = (2 * r) * scale + 2.2
        w_in = (2 * r) * scale - 1.6
        Q = P[:n + 1]
        for i, j in _chunks(Q):
            a, b = max(0, i - 1), min(len(Q) - 1, j + 1)
            ends = [Q[i] if i == 0 else (Q[i] + Q[i - 1]) / 2] + list(Q[i + 1:j]) + \
                   [Q[j] if j == len(Q) - 1 else (Q[j] + Q[j + 1]) / 2]
            out_pts = ' '.join('%.1f,%.1f' % (X(p[0]), Y(p[1])) for p in ends)
            in_pts = ' '.join('%.1f,%.1f' % (X(p[0]), Y(p[1])) for p in Q[a:b + 1])
            capo = 'round' if (i == 0 or j == len(Q) - 1) else 'butt'
            z = float(Q[i:j + 1, 2].mean())
            items.append((z, '<polyline points="%s" fill="none" stroke="%s" stroke-width="%.1f" stroke-linecap="%s" stroke-linejoin="round"/>'
                          '<polyline points="%s" fill="none" stroke="%s" stroke-width="%.1f" stroke-linecap="round" stroke-linejoin="round"/>'
                          % (out_pts, edge, w_out, capo, in_pts, col, w_in)))
        # end marker on the moving end
        if step_index is not None and vis[k] < 0.999:
            p = Q[-1]
            items.append((float(p[2]) + 0.01, '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (X(p[0]), Y(p[1]), r * scale * 0.55, edge)))
    items.sort(key=lambda t: t[0])
    body = ''.join(s for _, s in items)
    if labels and step_index is not None and tags_for_step:
        for t in step_tags(knot, built, step_index):
            body += _tag_svg(X(t['p'][0]), Y(t['p'][1]) - r * scale - 4, t['over'])
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.0f %.0f" class="diagram" role="img">%s</svg>' % (W, H, body)


def _tag_svg(x, y, over):
    txt = 'OVER' if over else 'UNDER'
    w = 44 if over else 52
    cls = 'tg-over' if over else 'tg-under'
    return ('<g class="%s"><rect x="%.1f" y="%.1f" width="%d" height="18" rx="3"/>'
            '<path d="M%.1f %.1fl5 6l5 -6z"/><text x="%.1f" y="%.1f">%s</text></g>'
            % (cls, x - w / 2, y - 24, w, x - 5, y - 6, x, y - 11, txt))


def _obj_extent(ob):
    c = ob['c']
    if ob['type'] == 'pole':
        L, rad = ob['len'] / 2, ob['radius']
        if ob['axis'] == 'y':
            return np.array([c[0] - rad, c[0] + rad]), np.array([c[1] - L, c[1] + L])
        return np.array([c[0] - L, c[0] + L]), np.array([c[1] - rad, c[1] + rad])
    if ob['type'] == 'ring':
        e = ob['radius'] + ob['tube']
        return np.array([c[0] - e, c[0] + e]), np.array([c[1] - e, c[1] + e])
    return np.array([c[0]]), np.array([c[1]])


def _obj_svg(ob, X, Y, scale):
    c = ob['c']
    if ob['type'] == 'pole':
        L, rad = ob['len'] / 2, ob['radius']
        if ob['axis'] == 'y':
            x, y, w, h = X(c[0] - rad), Y(c[1] + L), 2 * rad * scale, 2 * L * scale
        else:
            x, y, w, h = X(c[0] - L), Y(c[1] + rad), 2 * L * scale, 2 * rad * scale
        return [(0.0, '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" class="obj-pole"/>' % (x, y, w, h))]
    if ob['type'] == 'ring':
        cx, cy = X(c[0]), Y(c[1])
        return [(-0.001, '<circle cx="%.1f" cy="%.1f" r="%.1f" class="obj-ring" stroke-width="%.1f" fill="none"/>'
                 % (cx, cy, ob['radius'] * scale, 2 * ob['tube'] * scale))]
    return []


# ---------------------------------------------------------------- export for the 3D viewer

def step_tags(knot, built, i):
    """Over/under tags for one step: skip crossings hidden behind an object,
    merge tags that sit on top of each other (doubled strands)."""
    st = knot['steps'][i]
    if st.get('notags'):
        return []
    has_obj = bool(knot.get('objects'))
    out = []
    for c in built['crossings']:
        if c['step'] != i:
            continue
        if has_obj and min(c['za'], c['zb']) < 0:
            continue
        p = [round(float(c['xy'][0]), 3), round(float(c['xy'][1]), 3), round(c['top'], 3)]
        if any(math.dist(p[:2], t['p'][:2]) < 0.55 and t['over'] == bool(c['mover_over']) for t in out):
            continue
        out.append({'p': p, 'over': bool(c['mover_over'])})
    return out


def export(knot, built):
    ropes = []
    for k, P in enumerate(built['ropes']):
        Q = P[::2] if len(P) % 2 == 1 else np.vstack([P[::2], P[-1:]])
        ropes.append({'color': knot['ropes'][k].get('color', 'a'),
                      'pts': [round(float(v), 3) for v in Q.reshape(-1)]})
    steps = []
    for i, st in enumerate(built['steps']):
        tags = step_tags(knot, built, i)
        steps.append({'vis': [round(v, 4) for v in st['vis']], 'tags': tags,
                      'tighten': bool(st.get('tighten'))})
    return {'r': built['r'], 'ropes': ropes, 'objects': knot.get('objects', []), 'steps': steps,
            'view': knot.get('view', {})}
