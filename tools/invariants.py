"""Print the topology of knot models, for recording expected values and for the
two-model agreement rule (two independently drawn models must print the same).

    python3 tools/invariants.py <slug> [<slug> ...]

Per rope: knot type with the old outside closure and with the fixed rule
(closed above the drawing). For two ropes: the fixed-rule link of rope 0
(above) and rope 1 (below), and the model's own whole closure with a validity check
(one closed loop must have whole powers of t; half powers mean the joining arcs
cross the drawing).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build  # noqa: E402
import knotlib  # noqa: E402


def name_of(V):
    for k in knotlib.KNOWN:
        if knotlib.knot_type_ok(V, k):
            return k
    return '?'


def show(slug):
    k = next(x for x in build.KNOTS if x['slug'] == slug)
    knot, built = build.build_knot(k)
    ropes = built['ropes']
    print('%s  (%d ropes, %d crossings)' % (slug, len(ropes), len(built['crossings'])))
    if len(built['crossings']) > 22:
        print('  too many crossings for the state sum; picture test only')
        return
    for i in range(len(ropes)):
        Vo = knotlib.jones([ropes[i]], [(0, 1)])
        Vf = knotlib.rope_alone(ropes, i)
        print('  rope %d: outside closure %-7s fixed rule %-7s %s' % (
            i, name_of(Vo), name_of(Vf), '' if name_of(Vo) == name_of(Vf) else '<- differ'))
    if len(ropes) == 2:
        V, lk = knotlib.link_pair(ropes)
        print('  link 0 above / 1 below: lk %d  jones %s' % (lk, knotlib.jones_key_str(V)))
    order = knot.get('closure', [(0, 1)])
    V = knotlib.jones(knot.get('jones_ropes') or ropes, order)
    valid = not any(e % 4 for e in V)
    print('  whole closure %s: %s%s' % (order, name_of(V) if valid else '-',
                                       '' if valid else '  (not a valid diagram: joining arcs cross the drawing)'))


for s in sys.argv[1:]:
    show(s)
