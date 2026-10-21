"""Proves the knot-type machinery before any knot model relies on it.

1. Reference table: every KNOWN entry that has a standard planar diagram code
   (PD code) is recomputed here with an independent Kauffman-bracket routine.
2. Geometry: knotlib.jones_loops on closed curves whose type is known
   (torus knots, the figure-eight curve, Hopf link, unlink).
3. Closure rule: open ropes closed by close_above_below give the expected link.

Run: python3 tests/check_jones.py   (exit 1 on any failure; build.py runs it first)
"""
import math
import os
import sys
from itertools import product

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import knotlib  # noqa: E402

FAIL = []


def check(name, ok, detail=''):
    print('%-52s %s %s' % (name, 'ok' if ok else 'FAIL', detail))
    if not ok:
        FAIL.append(name)


# ---------------------------------------------------------------- 1. table vs PD codes

def pd_jones(pd):
    """Jones polynomial from a PD code X[a,b,c,d] (a = incoming under strand,
    counterclockwise). Independent of knotlib's geometric reader."""
    n = len(pd)
    m = 2 * n
    br = {}
    for st in product((0, 1), repeat=n):
        par = list(range(m + 1))

        def f(x):
            while par[x] != x:
                x = par[x]
            return x
        na = 0
        for (a, b, c, d), s in zip(pd, st):
            if s == 0:
                par[f(a)] = f(b); par[f(c)] = f(d); na += 1
            else:
                par[f(a)] = f(d); par[f(b)] = f(c)
        loops = len({f(x) for x in range(1, m + 1)})
        p = {na - (n - na): 1}
        for _ in range(loops - 1):
            q = {}
            for e, v in p.items():
                q[e + 2] = q.get(e + 2, 0) - v
                q[e - 2] = q.get(e - 2, 0) - v
            p = q
        for e, v in p.items():
            br[e] = br.get(e, 0) + v
    w = sum(1 if (b - d) % m == 1 else -1 for (a, b, c, d) in pd)
    out = {}
    for e, v in br.items():
        if v:
            k = -(e - 3 * w)
            out[k] = out.get(k, 0) + v * (-1) ** (w % 2)
    return {k: v for k, v in out.items() if v}


def torus2_pd(n):
    m = 2 * n
    wrap = lambda x: (x - 1) % m + 1
    return [tuple(wrap(v) for v in (2 * i - 1, 2 * i - 1 + n, 2 * i, 2 * i + n)) for i in range(1, n + 1)]


PD = {
    '3_1': torus2_pd(3),
    '4_1': [(4, 2, 5, 1), (8, 6, 1, 5), (6, 3, 7, 4), (2, 7, 3, 8)],
    '5_1': torus2_pd(5),
    '5_2': [(1, 5, 2, 4), (3, 9, 4, 8), (5, 1, 6, 10), (7, 3, 8, 2), (9, 7, 10, 6)],
    '6_1': [(1, 4, 2, 5), (7, 10, 8, 11), (3, 9, 4, 8), (9, 3, 10, 2), (5, 12, 6, 1), (11, 6, 12, 7)],
    '7_1': torus2_pd(7),
    '9_1': torus2_pd(9),
}

for name, pd in PD.items():
    V = pd_jones(pd)
    check('table %s matches its PD code' % name, knotlib.knot_type_ok(V, name), knotlib.jones_str(V))
    check('table %s value 1 at t=1' % name, sum(knotlib.KNOWN[name].values()) == 1)
check('table 5_2 determinant is 7', knotlib.jones_det(knotlib.KNOWN['5_2']) == 7)
untested = sorted(set(knotlib.KNOWN) - set(PD) - {'unknot', 'square', 'granny', 'surgeon', 'surgeon2', '8_18'})
check('every table entry is proven (PD code, or braid for 8_18)', not untested, ', '.join(untested))

# ---------------------------------------------------------------- 2. geometry → type


def curve(fn, n=600):
    s = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.array([fn(t) for t in s])


def torus(p, q, n=900):
    return curve(lambda t: ((2 + math.cos(q * t)) * math.cos(p * t),
                            (2 + math.cos(q * t)) * math.sin(p * t), math.sin(q * t)), n)


fig8 = curve(lambda t: ((2 + math.cos(2 * t)) * math.cos(3 * t),
                        (2 + math.cos(2 * t)) * math.sin(3 * t), math.sin(4 * t)), 900)

for label, L, name in [('torus (3,2) curve', torus(3, 2), '3_1'),
                       ('torus (5,2) curve', torus(5, 2), '5_1'),
                       ('figure-eight curve', fig8, '4_1')]:
    V, _ = knotlib.jones_loops([L])
    check('jones_loops: %s is %s' % (label, name), knotlib.knot_type_ok(V, name), knotlib.jones_str(V))

circA = curve(lambda t: (math.cos(t), math.sin(t), 0.0), 240)
circB = curve(lambda t: (1 + math.cos(t), 0.3 * math.sin(t), math.sin(t)), 240)
HOPF = [{2: -1, 10: -1}, {-2: -1, -10: -1}]
V, lk = knotlib.jones_loops([circA, circB])
check('jones_loops: Hopf link', V in HOPF and abs(lk) == 1, '%s lk=%d' % (knotlib.jones_str(V), lk))
far = circB + np.array([5.0, 0, 0])
V, lk = knotlib.jones_loops([circA, far])
check('jones_loops: unlink', V == {2: -1, -2: -1} and lk == 0, '%s lk=%d' % (knotlib.jones_str(V), lk))

# ---------------------------------------------------------------- 3. closure rule on open ropes
# Cut a gap out of each circle of the Hopf link: the open arcs, closed by the
# rule (A above, B below), must give the Hopf link again; far apart, the unlink.


def open_arc(L, gap_at, width=0.6):
    ang = np.arctan2(L[:, 1] - L[:, 1].mean(), L[:, 0] - L[:, 0].mean())
    d = np.abs((ang - gap_at + math.pi) % (2 * math.pi) - math.pi)
    keep = d > width
    idx = np.nonzero(keep)[0]
    start = idx[np.argmax(np.diff(np.r_[idx, idx[0] + len(L)]))] + 1  # first index after the gap
    order = [(start + j) % len(L) for j in range(len(L)) if keep[(start + j) % len(L)]]
    return L[order]


A = open_arc(circA, math.pi / 2)
B = open_arc(circB, -math.pi / 2)
V, lk = knotlib.link_pair([A, B])
check('closure rule: open Hopf arcs close to Hopf', V in HOPF and abs(lk) == 1, '%s lk=%d' % (knotlib.jones_str(V), lk))
V, lk = knotlib.link_pair([A, B + np.array([6.0, 0, 0])])
check('closure rule: far-apart arcs close to unlink', V == {2: -1, -2: -1} and lk == 0, '%s lk=%d' % (knotlib.jones_str(V), lk))
T = open_arc(torus(3, 2), 0.3, 0.15)
check('closure rule: open trefoil arc closes to 3_1', knotlib.knot_type_ok(knotlib.rope_alone([T], 0), '3_1'))

# ---------------------------------------------------------------- 4. 8_18 from its braid
# 8_18 has no PD code here; it is the closure of the 3-braid (s1 s2^-1)^4.
# Strands sit on rings of radius 1, 2, 3 round an axis; each sector of the
# annulus performs one generator. jones_loops is proven by sections 2-3.


def closed_braid(word, nstr, per=41):
    pos = list(range(nstr))            # pos[strand] = ring index
    paths = [[] for _ in range(nstr)]
    nsec = len(word)
    for k, (gi, sg) in enumerate(word):
        for j in range(per):
            s = j / per
            th = 2 * math.pi * (k + s) / nsec
            for st in range(nstr):
                r, z = pos[st] + 1.0, 0.0
                if pos[st] == gi:          # moves outward
                    r, z = gi + 1.0 + s, 0.4 * sg * math.sin(math.pi * s)
                elif pos[st] == gi + 1:    # moves inward
                    r, z = gi + 2.0 - s, -0.4 * sg * math.sin(math.pi * s)
                paths[st].append((r * math.cos(th), r * math.sin(th), z))
        for st in range(nstr):
            if pos[st] == gi:
                pos[st] = gi + 1
            elif pos[st] == gi + 1:
                pos[st] = gi
    # follow strands round the closure: strand st ends on ring pos[st], where strand starting there begins
    start_of = {ring: st for st, ring in enumerate(range(nstr))}
    loops, seen = [], set()
    for st0 in range(nstr):
        if st0 in seen:
            continue
        pts, st = [], st0
        while st not in seen:
            seen.add(st)
            pts += paths[st]
            st = start_of[pos[st]]
        loops.append(np.array(pts))
    return loops


L = closed_braid([(0, 1), (1, -1)] * 4, 3)
V, _ = knotlib.jones_loops(L)
check('8_18 braid closure: one component', len(L) == 1)
check('table 8_18 matches the braid (s1 s2^-1)^4', knotlib.knot_type_ok(V, '8_18'), knotlib.jones_str(V))
L = closed_braid([(0, 1)] * 3, 2)
check('braid check: s1^3 closes to 3_1', knotlib.knot_type_ok(knotlib.jones_loops(L)[0], '3_1'))
L = closed_braid([(0, 1), (1, -1)] * 2, 3)
check('braid check: (s1 s2^-1)^2 closes to 4_1', knotlib.knot_type_ok(knotlib.jones_loops(L)[0], '4_1'))
L = closed_braid([(0, 1)] * 3, 2, per=40)
check('vertex-crossing guard: s1^3 sampled on its crossings', knotlib.knot_type_ok(knotlib.jones_loops(L)[0], '3_1'))

if FAIL:
    print('\n%d check(s) failed' % len(FAIL))
    sys.exit(1)
print('\nall jones checks passed')
