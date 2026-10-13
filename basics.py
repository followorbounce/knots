"""The six primer pages under /basics/. Original text; diagrams drawn by the engine."""
import html
import math

import knotlib
from knotlib import coil_y, R

E = html.escape

PAGES = [
    {'slug': 'rope-construction', 'title': 'How rope is made', 'short': 'Construction',
     'intro': 'Laid, braided and kernmantle rope behave differently in your hands and in a knot.'},
    {'slug': 'rope-materials', 'title': 'What rope is made of', 'short': 'Materials',
     'intro': 'Natural and synthetic fibres: which stretch, which float, which slip.'},
    {'slug': 'rope-care', 'title': 'Looking after rope', 'short': 'Care',
     'intro': 'Inspect, clean and retire rope before it lets you down.'},
    {'slug': 'coiling-storing', 'title': 'Coiling and storing', 'short': 'Coiling',
     'intro': 'Coil it so it runs free next time, and store it where it will last.'},
    {'slug': 'terms', 'title': 'Words for the parts of a rope', 'short': 'Terms',
     'intro': 'Standing part, working end, bight, loop, turn. The words every step uses.'},
    {'slug': 'technique', 'title': 'Tying technique', 'short': 'Technique',
     'intro': 'Dress, set, leave a tail, and test. Good habits that make any knot better.'},
]


# ------------------------------------------------------------------ terms diagrams

def _anatomy():
    pts = [[-4.6, 0.0], [-3.2, 0.0], [-1.8, 0.0], [-0.7, 0.0], [-0.1, 0.38], [-0.7, 0.8], [-1.7, 0.85],
           [-2.4, 1.3], [-1.7, 1.78], [-0.2, 1.8], [1.0, 1.8], [1.9, 1.45], [1.75, 0.82], [1.15, 0.78], [0.92, 1.3],
           [1.05, 2.15], [1.6, 2.65], [2.6, 2.8], [3.6, 2.8]]
    knot = {'ropes': [{'color': 'a', 'pts': pts}], 'code': 'u', 'objects': [], 'steps': [{'show': {0: 'all'}}]}
    parts = [('standing', 'Standing part', 0, 2), ('bight', 'Bight', 2, 6), ('loop', 'Loop', 9, 16),
             ('working', 'Working end', 16, 18)]
    return knot, parts


def _turns():
    rho = 0.45 + R + 0.015
    P = math.pi
    turn = [[-3.6, 0.75, -0.2], [-2.6, 0.55, -0.2]] + coil_y(-1.3, 0, rho, -0.5 * P, 1.5 * P, 0.4, -0.4, n=30) + \
        [[-2.6, -0.6, 0.2], [-3.6, -0.85, 0.2]]
    rt = [[3.6, 0.95, -0.2], [2.6, 0.8, -0.2]] + coil_y(1.3, 0, rho, 0.5 * P, -3.5 * P, 0.7, -0.7, n=60) + \
        [[2.6, -0.85, 0.2], [3.6, -1.05, 0.2]]
    knot = {'ropes': [{'color': 'a', 'pts': turn}, {'color': 'b', 'pts': rt}], 'code': None,
            'objects': [{'type': 'pole', 'axis': 'y', 'c': [-1.3, 0, 0], 'radius': 0.45, 'len': 3.0},
                        {'type': 'pole', 'axis': 'y', 'c': [1.3, 0, 0], 'radius': 0.45, 'len': 3.0}],
            'steps': [{'show': {0: 'all', 1: 'all'}}]}
    return knot


def _highlight_svg(knot, built, parts, scale=62):
    svg = knotlib.svg_diagram(knot, built, None, scale=scale, labels=False)
    import numpy as np
    P = built['ropes'][0]
    allp = np.vstack(built['ropes'])
    x0 = allp[:, 0].min() - built['r'] - 0.6
    y1 = allp[:, 1].max() + built['r'] + 0.6
    ctrl_s = knotlib.ctrl_arc_positions(knot['ropes'][0]['pts'])
    total = ctrl_s[-1]
    over = ''
    for key, label, a, b in parts:
        ia = int(round(ctrl_s[a] / total * (len(P) - 1)))
        ib = int(round(ctrl_s[b] / total * (len(P) - 1)))
        pts = ' '.join('%.1f,%.1f' % ((p[0] - x0) * scale, (y1 - p[1]) * scale) for p in P[ia:ib + 1])
        over += '<polyline class="hl" data-term="%s" points="%s"/>' % (key, pts)
    return svg.replace('</svg>', over + '</svg>')


# ------------------------------------------------------------------ construction cross-sections

def _circle(cx, cy, r, cls):
    return '<circle cx="%.1f" cy="%.1f" r="%.1f" class="%s"/>' % (cx, cy, r, cls)


def _strand(cx, cy, r, cls):
    out = _circle(cx, cy, r, cls)
    for k in range(7):
        if k == 0:
            out += _circle(cx, cy, r * 0.28, 'yarn')
        else:
            a = k * math.pi / 3
            out += _circle(cx + r * 0.55 * math.cos(a), cy + r * 0.55 * math.sin(a), r * 0.28, 'yarn')
    return out


def section_svg(kind):
    c, out = 90, ''
    if kind == 'laid':
        for k in range(3):
            a = -math.pi / 2 + k * 2 * math.pi / 3
            out += _strand(c + 30 * math.cos(a), c + 30 * math.sin(a), 32, 's%d' % k)
    elif kind == 'braid':
        for k in range(12):
            a = k * 2 * math.pi / 12
            out += _circle(c + 58 * math.cos(a), c + 58 * math.sin(a), 15, 's%d' % (k % 2))
    elif kind == 'double':
        for k in range(16):
            a = k * 2 * math.pi / 16
            out += _circle(c + 66 * math.cos(a), c + 66 * math.sin(a), 11, 's%d' % (k % 2))
        for k in range(8):
            a = k * 2 * math.pi / 8 + 0.2
            out += _circle(c + 34 * math.cos(a), c + 34 * math.sin(a), 13, 's2')
    elif kind == 'kern':
        for k in range(20):
            a = k * 2 * math.pi / 20
            out += _circle(c + 68 * math.cos(a), c + 68 * math.sin(a), 9.5, 's%d' % (k % 2))
        pos = [(0, 0)] + [(30 * math.cos(k * math.pi / 3), 30 * math.sin(k * math.pi / 3)) for k in range(6)]
        for x, y in pos:
            out += _strand(c + x, c + y, 15, 's2')
    elif kind == 'plait':
        for k in range(8):
            a = k * 2 * math.pi / 8 + math.pi / 8
            out += _circle(c + 44 * math.cos(a), c + 44 * math.sin(a), 22, 's%d' % (k // 2 % 2))
    return '<svg viewBox="0 0 180 180" class="xsec" role="img" aria-label="Cross-section">%s</svg>' % out


def side_svg(kind):
    """Schematic side view: strand pattern on a vertical rope."""
    w, h, out = 70, 220, ''
    clip = '<clipPath id="cl-%s"><rect x="5" y="0" width="%d" height="%d" rx="30"/></clipPath>' % (kind, w - 10, h)
    if kind == 'laid':
        for k in range(-6, 12):
            y = k * 30
            out += '<path d="M5 %d L65 %d L65 %d L5 %d Z" class="s%d"/>' % (y + 30, y - 30, y - 6, y + 54, k % 3)
    elif kind in ('braid', 'double', 'plait', 'kern'):
        step = 22 if kind != 'kern' else 14
        for k in range(-4, 16):
            y = k * step
            out += '<path d="M5 %d L35 %d L65 %d" class="b%d" fill="none"/>' % (y, y + step, y, k % 2)
            out += '<path d="M5 %d L35 %d L65 %d" class="b%d" fill="none"/>' % (y + step, y, y + step, (k + 1) % 2)
    return ('<svg viewBox="0 0 %d %d" class="side" role="img" aria-label="Side view"><defs>%s</defs>'
            '<g clip-path="url(#cl-%s)"><rect x="5" y="0" width="%d" height="%d" class="bg"/>%s</g>'
            '<rect x="5" y="0" width="%d" height="%d" rx="30" class="edge" fill="none"/></svg>'
            % (w, h, clip, kind, w - 10, h, out, w - 10, h))


CONSTRUCTIONS = [
    ('laid', 'Three-strand laid', 'Three strands twisted round each other, each strand itself twisted from yarns in the opposite direction. Most laid rope is right-hand laid: hold it vertical and the strands slope like the middle stroke of a Z.',
     'Grips knots well. Easy to splice by hand. Kinks and hockles if twisted against its lay.', 'Mooring and anchor lines, general work, traditional rigging.'),
    ('braid', 'Single braid', 'Eight, twelve or sixteen strands braided round a hollow centre, half going one way and half the other.',
     'Does not kink. Flexible. A hollow braid can be spliced by tucking the rope inside itself.', 'Light lines, cord, flag halyards, high-strength single braids.'),
    ('double', 'Double braid', 'A braided core inside a braided cover. Both share the load, so the rope is strong for its size.',
     'Smooth, round and firm. Runs well through blocks. Splicing it needs special tools.', 'Sheets and halyards on boats.'),
    ('kern', 'Kernmantle', 'A core (kern) of long parallel or twisted bundles carries most of the load, protected by a tightly braided sheath (mantle).',
     'Dynamic versions stretch to absorb a fall; static versions barely stretch. The sheath hides damage to the core.', 'Climbing, caving and rescue rope.'),
    ('plait', 'Eight-strand plaited', 'Four pairs of strands, two pairs twisted each way, plaited together.',
     'Very flexible and does not kink. Stows easily in a locker.', 'Anchor rodes and mooring lines.'),
]

MATERIALS = [
    ('Manila', 'Natural', 'Low', 'Absorbs water', 'Fair', 'Good', 'Stiff and rough on hands. Rots if stored wet.'),
    ('Sisal', 'Natural', 'Low', 'Absorbs water', 'Fair', 'Good', 'Cheaper and weaker than manila. Garden and craft use.'),
    ('Cotton', 'Natural', 'Moderate', 'Absorbs water', 'Poor', 'Very good', 'Soft and weak. Decorative work, sash cord.'),
    ('Hemp', 'Natural', 'Low', 'Absorbs water', 'Fair', 'Good', 'Strong for a natural fibre. Rots without care.'),
    ('Nylon (polyamide)', 'Synthetic', 'High', 'Sinks', 'Good', 'Good', 'Stretches to absorb shock. Somewhat weaker when wet.'),
    ('Polyester', 'Synthetic', 'Low', 'Sinks', 'Very good', 'Good', 'The all-rounder for boats: low stretch, wears well.'),
    ('Polypropylene', 'Synthetic', 'Moderate', 'Floats', 'Poor', 'Fair', 'Cheap and light. Melts easily; sunlight degrades it.'),
    ('HMPE', 'Synthetic', 'Very low', 'Floats', 'Good', 'Poor', 'Very strong for its weight but slippery: knots can slip, so it is usually spliced.'),
    ('Aramid', 'Synthetic', 'Very low', 'Sinks', 'Fair', 'Fair', 'Very strong and heat resistant. Weakened by repeated sharp bending; usually covered.'),
]


def _nav(cur):
    out = ''
    for p in PAGES:
        a = ' aria-current="page"' if p['slug'] == cur else ''
        out += '<a href="../%s/index.html"%s>%s</a>' % (p['slug'], a, E(p['short']))
    return '<nav class="subnav" aria-label="Basics">%s</nav>' % out


def _pager(i):
    prev_ = PAGES[i - 1] if i > 0 else None
    next_ = PAGES[i + 1] if i + 1 < len(PAGES) else None
    out = '<nav class="pager" aria-label="Next and previous">'
    out += ('<a href="../%s/index.html"><span>Previous</span>%s</a>' % (prev_['slug'], E(prev_['title']))) if prev_ else '<span></span>'
    out += ('<a href="../%s/index.html" class="next"><span>Next</span>%s</a>' % (next_['slug'], E(next_['title']))) if next_ else \
        '<a href="../../index.html" class="next"><span>Next</span>Start tying</a>'
    return out + '</nav>'


def body_for(slug):
    if slug == 'rope-construction':
        tabs = ''.join('<button type="button" role="tab" id="tab-%s" aria-selected="%s" aria-controls="pane-%s">%s</button>'
                       % (k, 'true' if i == 0 else 'false', k, E(t)) for i, (k, t, *_) in enumerate(CONSTRUCTIONS))
        panes = ''.join(
            '<div class="pane" role="tabpanel" id="pane-%s" aria-labelledby="tab-%s"%s><div class="pics">%s%s</div>'
            '<div class="ptext"><h3>%s</h3><p>%s</p><dl><dt>In use</dt><dd>%s</dd><dt>Typical jobs</dt><dd>%s</dd></dl></div></div>'
            % (k, k, '' if i == 0 else ' hidden', section_svg(k), side_svg(k), E(t), E(d), E(h), E(u))
            for i, (k, t, d, h, u) in enumerate(CONSTRUCTIONS))
        return f'''
<p>Rope starts as fibres. Fibres are spun into yarns, yarns are twisted or grouped into strands, and strands are laid, braided or plaited into rope. How that last step is done decides how the rope handles, how it takes a knot, and how you splice it.</p>
<div class="tabs" role="tablist" aria-label="Rope construction">{tabs}</div>
{panes}
<h2>Why it matters for knots</h2>
<p>Laid rope has a direction of twist. Coil it the same way as the lay (clockwise for right-hand rope) or it will kink. Braided rope has no lay, so coil it in figure-eights instead. A firm, smooth cover makes knots slip more easily than a soft, hairy one, so slippery rope needs more secure knots and longer tails.</p>'''
    if slug == 'rope-materials':
        rows = ''.join('<tr><th scope="row">%s</th><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % tuple(E(c) for c in m)
                       for m in MATERIALS)
        return f'''
<p>Natural fibres were the only choice until the middle of the twentieth century. Today most working rope is synthetic: stronger for its size, rot-proof, and available with exactly the stretch a job needs.</p>
<div class="tbl"><table>
<thead><tr><th scope="col">Fibre</th><th scope="col">Type</th><th scope="col">Stretch</th><th scope="col">In water</th><th scope="col">Sunlight</th><th scope="col">Holds knots</th><th scope="col">Notes</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="small">General guide only. Ropes of the same fibre differ by maker, construction and coating; check the maker’s data for loads.</p>
<h2>Choosing</h2>
<ul>
<li><b>Shock loads</b> (towing, anchoring, climbing falls): a rope that stretches, usually nylon.</li>
<li><b>Holding a position</b> (sheets, halyards, guy lines): low stretch, usually polyester.</li>
<li><b>On or in the water</b> (rescue throw lines, water-ski tow ropes): a rope that floats, usually polypropylene.</li>
<li><b>Craft and decorative knots</b>: cotton or soft braided polyester, which take a shape and hold it.</li>
</ul>
<p>Strength figures on a label are for new rope pulled straight. Knots, bends round small objects, wear, sunlight and age all reduce the strength you can actually use, which is why working loads are set well below breaking loads.</p>'''
    if slug == 'rope-care':
        return '''
<p>Rope fails at its weakest point, and damage is often hidden. A minute spent looking at a rope before you trust it is never wasted.</p>
<h2>Inspect</h2>
<ul class="checklist">
<li><label><input type="checkbox"> Run the whole length through your hands, feeling for flat, stiff or soft spots.</label></li>
<li><label><input type="checkbox"> Look for cuts, heavy fuzzing, glazed or melted areas, and broken yarns.</label></li>
<li><label><input type="checkbox"> On kernmantle rope, look for the core showing through the sheath.</label></li>
<li><label><input type="checkbox"> Check for discolouration from chemicals or long sun exposure.</label></li>
<li><label><input type="checkbox"> Open the strands of laid rope slightly: powdery fibres inside mean internal wear.</label></li>
</ul>
<h2>Clean and dry</h2>
<p>Rinse salt, grit and mud out with cool fresh water. A mild soap is fine; strong detergents and bleach are not. Dry rope loosely coiled, in the shade, away from heaters and direct sun.</p>
<h2>Avoid</h2>
<ul>
<li>Stepping on rope or dragging it over grit, which works sharp particles into the fibres.</li>
<li>Running rope over sharp edges. Protect it with a sleeve or padding.</li>
<li>Rope running fast over rope, which melts synthetic fibres through friction.</li>
<li>Contact with acids, solvents and fuels. Battery acid can destroy nylon with little visible sign.</li>
</ul>
<h2>Retire it</h2>
<p>Replace any rope with damage you can see or feel. Ropes used to hold people have extra rules: keep a log, follow the maker’s lifespan, and retire a rope after a severe fall or any doubt about its history.</p>'''
    if slug == 'coiling-storing':
        return '''
<p>A good coil comes out of the bag, off the hook or out of the locker without a tangle. A bad one costs you time just when you need the rope.</p>
<h2>Coils</h2>
<ol class="numbered">
<li><b>Laid rope: coil with the lay.</b> For right-hand laid rope, coil clockwise. Give each loop a small twist with your fingers so it lies flat.</li>
<li><b>Braided rope: figure-eight coil.</b> Lay the loops alternately to one side and the other, like an 8. The twists cancel out, so the rope will not kink.</li>
<li><b>Butterfly coil.</b> Drape the rope back and forth across your shoulders or hand in long bights. Quick, kink-free, and easy to carry as a pack. Common for climbing rope.</li>
<li><b>Finishing a coil.</b> Wrap the last part of the rope several times round the middle of the coil, pass a bight through the top, and pull the end through that bight.</li>
<li><b>Flaking.</b> To have rope ready to run, lay it on the ground or deck in a loose pile, end to end, so it pays out without snagging.</li>
</ol>
<h2>Storage</h2>
<ul>
<li>Clean and dry first. Natural fibres rot if stored damp; synthetics grow mildew on dirt.</li>
<li>Somewhere cool, dark and airy. Sunlight slowly weakens most fibres.</li>
<li>Hang coils or keep them in a bag, off the floor and away from chemicals.</li>
<li>Seal or whip the ends so they cannot unravel.</li>
</ul>'''
    if slug == 'terms':
        return '''
<p>Instructions for knots use a small set of words for the parts of a rope. Select a word to see it on the drawing.</p>
<div class="anat" id="anat">
  <div class="anat-terms" role="group" aria-label="Parts of a rope">
    <button type="button" data-term="standing" aria-pressed="false"><b>Standing part</b><span>The long, inactive part of the rope, often the part that takes the load.</span></button>
    <button type="button" data-term="bight" aria-pressed="false"><b>Bight</b><span>The rope folded back on itself in a U, without crossing.</span></button>
    <button type="button" data-term="loop" aria-pressed="false"><b>Loop</b><span>A circle of rope where it crosses itself.</span></button>
    <button type="button" data-term="working" aria-pressed="false"><b>Working end</b><span>The end you tie with. Also the tail, the short end left after the knot.</span></button>
  </div>
  <div class="anat-fig">{ANATOMY}</div>
</div>
<h2>Turns</h2>
<figure class="turns">{TURNS}<figcaption><b>Turn</b> (left): the rope goes round the object once. <b>Round turn</b> (right): it goes round a second time, so it grips the object all the way round and can hold a load while you finish the knot.</figcaption></figure>
<h2>More words</h2>
<dl class="gloss">
<dt>Knot</dt><dd>Strictly, a knot tied in one rope, such as a stopper or a loop. Loosely, anything tied.</dd>
<dt>Bend</dt><dd>A knot that joins two ropes end to end.</dd>
<dt>Hitch</dt><dd>A knot that ties a rope to something: a post, ring, rail or another rope.</dd>
<dt>Binding knot</dt><dd>A knot that holds an object or bundle together.</dd>
<dt>Riding turn</dt><dd>A turn that crosses over another, as in a Clove Hitch.</dd>
<dt>Nip</dt><dd>The place where one part of a knot presses on another and holds it by friction.</dd>
<dt>Lay</dt><dd>The direction the strands of laid rope are twisted.</dd>
<dt>Tying in the bight</dt><dd>Tying a knot without using an end, with a doubled part of the rope instead.</dd>
<dt>Slipped</dt><dd>Finished with a bight instead of the end, so one pull on the end unties it.</dd>
<dt>Dress</dt><dd>Arrange the parts of a knot so they lie neatly, without unwanted crossings.</dd>
<dt>Set</dt><dd>Tighten a dressed knot by pulling each part in turn.</dd>
<dt>Whipping</dt><dd>Turns of thin twine round a rope end to stop it unravelling.</dd>
</dl>'''
    if slug == 'technique':
        return '''
<p>A knot that is tied right but finished badly can still fail. These habits apply to every knot in this guide.</p>
<ol class="numbered">
<li><b>Leave enough end.</b> Start with more working end than you think you need. Running out halfway through is the most common reason knots end up tied wrong.</li>
<li><b>Dress it.</b> Before tightening, arrange every part so it lies where it should. Parallel strands stay parallel; nothing is twisted or crossed by accident.</li>
<li><b>Work out the slack.</b> Tighten a little at a time, pulling each part in turn and moving the slack toward the end. Yanking both ends at once can capsize a knot into a different shape.</li>
<li><b>Set it.</b> Give the finished knot a firm pull on every part it has. A knot that settles under its first load can loosen.</li>
<li><b>Leave a tail.</b> At least several rope-widths, more for slippery or stiff rope and for anything that holds people.</li>
<li><b>Check it.</b> Compare it to a picture. Look for the right number of crossings and parts in the right places. For life-safety knots, have someone else check too.</li>
</ol>
<h2>Rope ends</h2>
<p>A cut end unravels quickly. Seal synthetic rope by melting the end with a flame or hot knife, tape it as a quick fix, or whip it with thin twine for a lasting finish. Natural rope cannot be melted, so tape or whip it.</p>
<h2>Practising</h2>
<p>Learn a knot with a short length of soft rope about as thick as your finger, at a table. Tie it until you can do it without looking, then tie it with the other hand, behind your back, and in the dark. Use Mirror on any knot page to see it the other way round.</p>'''
    return ''


def build(page):
    paths = []
    anat_knot, parts = _anatomy()
    anat_svg = _highlight_svg(anat_knot, knotlib.build(anat_knot), parts)
    tk = _turns()
    turns_svg = knotlib.svg_diagram(tk, knotlib.build(tk), None, scale=56, labels=False)
    cards = ''.join('<li><a href="%s/index.html"><span class="eyebrow">%d</span><h3>%s</h3><p>%s</p></a></li>'
                    % (p['slug'], i + 1, E(p['title']), E(p['intro'])) for i, p in enumerate(PAGES))
    body = f'''
<section class="page-head"><p class="eyebrow">Basics</p><h1>Before you tie</h1>
<p class="lede">Six short pages on rope itself and on the words and habits every knot relies on. Read them in order or dip in.</p></section>
<ol class="basics-grid">{cards}</ol>'''
    paths.append(page('basics/index.html', 'Basics | Knot Atlas', 'Rope construction, materials, care, coiling, terms and technique.',
                      body, nav='basics', cls='p-basics'))
    for i, p in enumerate(PAGES):
        content = body_for(p['slug']).replace('{ANATOMY}', anat_svg).replace('{TURNS}', turns_svg)
        body = f'''
<section class="page-head"><p class="eyebrow"><a href="../index.html">Basics</a> · {i + 1} of {len(PAGES)}</p><h1>{E(p['title'])}</h1>
<p class="lede">{E(p['intro'])}</p>{_nav(p['slug'])}</section>
<section class="prose">{content}</section>
{_pager(i)}'''
        paths.append(page('basics/%s/index.html' % p['slug'], '%s | Knot Atlas' % p['title'], p['intro'], body,
                          nav='basics', cls='p-basics', scripts='<script src="{up}assets/site.js"></script>'))
    return paths
