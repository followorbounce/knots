"""Dev preview: python3 tools/preview.py <geometry_fn> [outdir]

Builds one knot's geometry, prints the checker report and crossing list,
and writes a PNG of the finished diagram with each crossing numbered in
traversal order (plus a second view from above, x-z, to check depth).
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np  # noqa: E402
import geometry  # noqa: E402
import knotlib  # noqa: E402


def main():
    name = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else '/tmp'
    g = getattr(geometry, name)()
    marks = sorted(g['marks'].items(), key=lambda kv: (kv[1][0], kv[1][1]))
    steps = [{'show': {m[1][0]: m[1][1]}, 'text': m[0]} for m in marks]
    knot = dict(g, steps=steps)
    built = knotlib.build(knot)
    print('problems:', built['problems'] or 'none')
    order = []
    for ci, c in enumerate(built['crossings']):
        order.append(((c['ra'], c['ia']), ci))
        order.append(((c['rb'], c['ib']), ci))
    order.sort()
    seq = []
    for (rope, f), ci in order:
        c = built['crossings'][ci]
        me_a = (rope, f) == (c['ra'], c['ia'])
        over = c['a_over'] if me_a else not c['a_over']
        seq.append('r%d@%d:%s#%d' % (rope, int(f), 'O' if over else 'U', ci))
    print('walk:', ' '.join(seq))
    svg = knotlib.svg_diagram(knot, built, None, scale=70, labels=False)
    # number crossings
    allp = np.vstack(built['ropes'])
    xs, ys = allp[:, 0], allp[:, 1]
    for ob in knot.get('objects', []):
        ex = knotlib._obj_extent(ob)
        xs = np.concatenate([xs, ex[0]]); ys = np.concatenate([ys, ex[1]])
    x0 = xs.min() - built['r'] - 0.6
    y1 = ys.max() + built['r'] + 0.6
    lab = ''
    for ci, c in enumerate(built['crossings']):
        lab += '<text x="%.0f" y="%.0f" font-size="15" fill="#c00" font-family="sans-serif">%d</text>' % (
            (c['xy'][0] - x0) * 70 + 8, (y1 - c['xy'][1]) * 70 - 8, ci)
    svg = svg.replace('</svg>', lab + '</svg>')
    style = '<style>.obj-pole{fill:#d8c39a;stroke:#6b5a3a}.obj-ring{stroke:#999}</style>'
    svg = svg.replace('role="img">', 'role="img"><rect width="100%" height="100%" fill="#fff"/>' + style)
    p = os.path.join(out, name + '.svg')
    open(p, 'w').write(svg)
    subprocess.run(['magick', p, os.path.join(out, name + '.png')], check=True)
    # top view: swap y and z
    k2 = dict(knot)
    b2 = dict(built, ropes=[P[:, [0, 2, 1]] for P in built['ropes']])
    k2['objects'] = []
    svg2 = knotlib.svg_diagram(k2, b2, None, scale=50, labels=False)
    svg2 = svg2.replace('role="img">', 'role="img"><rect width="100%" height="100%" fill="#fff"/>')
    p2 = os.path.join(out, name + '_top.svg')
    open(p2, 'w').write(svg2)
    subprocess.run(['magick', p2, os.path.join(out, name + '_top.png')], check=True)
    print('wrote', os.path.join(out, name + '.png'))


if __name__ == '__main__':
    main()
