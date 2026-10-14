#!/usr/bin/env python3
"""Build the Knot Atlas site.

    python3 build.py           build everything
    python3 build.py --check   run the geometry checker only (exit 1 on problems)

Sources: knots.py (content), geometry.py (rope models), knotlib.py (engine),
basics.py (primer pages). Everything under knots/, basics/, finder/, about/ and
index.html is generated; edit the sources, not the output.
"""
import html
import json
import os
import sys

import geometry
import knotlib
from knots import KNOTS, CHAPTERS, ACTIVITIES, JOBS, SAFETY
import basics

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://followorbounce.github.io/knots/'
NAME = 'Knot Atlas'
E = html.escape

HEAD = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta name="theme-color" content="#172326">
<link rel="icon" href="{up}assets/icon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="{up}assets/site.css">
<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "bba4e16a7d9b4d9985eda0cda2624e60"}}'></script>
</head>
<body class="{cls}">
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <a class="brand" href="{up}index.html"><svg viewBox="0 0 32 32" aria-hidden="true"><use href="{up}assets/icon.svg#mark"/></svg><span>Knot Atlas</span></a>
  <nav aria-label="Main">
    <a href="{up}index.html"{n_knots}>Knots</a>
    <a href="{up}finder/index.html"{n_finder}>Finder</a>
    <a href="{up}basics/index.html"{n_basics}>Basics</a>
    <a href="{up}about/index.html"{n_about}>About</a>
  </nav>
</header>
<main id="main">
'''

FOOT = '''</main>
<footer class="foot">
  <p>Knot Atlas. Every drawing is generated from a 3D rope model; every word is written for this guide.</p>
  <p><a href="{up}about/index.html">Method, safety and credits</a></p>
</footer>
{scripts}
</body>
</html>
'''


def page(path, title, desc, body, nav='', cls='', scripts=''):
    depth = path.count('/')
    up = '../' * depth
    canon = SITE + (path[:-len('index.html')] if path.endswith('index.html') else path)
    marks = {k: '' for k in ('n_knots', 'n_finder', 'n_basics', 'n_about')}
    if nav:
        marks['n_' + nav] = ' aria-current="page"'
    out = HEAD.format(title=E(title), desc=E(desc), canon=canon, up=up, cls=cls, **marks) + body + \
        FOOT.format(up=up, scripts=scripts.replace('{up}', up))
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w') as f:
        f.write(out)
    return path


# ------------------------------------------------------------------ knots

def resolve_steps(k, g):
    marks = g['marks']
    steps = []
    for st in k['steps']:
        at, text = st[0], st[1]
        opts = st[2] if len(st) > 2 else {}
        show = {}
        if at == 'all':
            show = {i: 'all' for i in range(len(g['ropes']))}
        elif isinstance(at, str):
            r, i = marks[at]
            show = {r: i}
        elif 'f' in at:
            fr = g['fractions'][at['f']]
            show = {i: fr for i in range(len(g['ropes']))}
        elif 'rf' in at:
            r, fr = g['rope_fractions'][at['rf']]
            show = {i: 'all' for i in range(r)}
            show[r] = float(fr)
        else:
            for name in at:
                r, i = marks[name]
                show[r] = i
        steps.append(dict(opts, show=show, text=text))
    # the last step always shows everything
    return steps


def build_knot(k):
    g = getattr(geometry, k['geo'])()
    knot = dict(g, steps=resolve_steps(k, g))
    built = knotlib.build(knot)
    return knot, built


DOTS = {1: 'Easy', 2: 'Intermediate', 3: 'Advanced'}

GLOSS = [
    ('standing part', 'The long, inactive part of the rope.'),
    ('working end', 'The end you tie with.'),
    ('round turn', 'The rope goes round an object twice, gripping it all the way round.'),
    ('half hitch', 'A single turn round something, with the end passed under itself.'),
    ('bight', 'The rope folded back on itself in a U, without crossing.'),
]


def gloss(text, up):
    """Escape step text and link the first use of each glossary term."""
    import re
    out = E(text)
    for term, tip in GLOSS:
        pat = re.compile(r'\b(%s)\b' % re.escape(term), re.I)
        out, n = pat.subn(lambda m: '<a class="term" href="%sbasics/terms/index.html" title="%s">%s</a>'
                          % (up, E(tip), m.group(1)), out, count=1)
    return out


def difficulty(n):
    return '<span class="dots" title="%s">%s%s</span> %s' % (DOTS[n], '●' * n, '○' * (3 - n), DOTS[n])


def chips(k, up):
    ch = CHAPTERS[k['chapter']][0]
    out = ['<a class="chip chip-ch" href="%sindex.html#%s">%s</a>' % (up, k['chapter'], ch)]
    out += ['<span class="chip">%s</span>' % a for a in k['acts']]
    return ''.join(out)


def knot_page(k, knot, built, by_slug):
    up = '../../'
    data = knotlib.export(knot, built)
    data['texts'] = [s['text'] for s in knot['steps']]
    data['name'] = k['name']
    nsteps = len(knot['steps'])
    diagrams = ''.join('<figure class="dg" data-step="%d"%s>%s</figure>' % (
        i, '' if i == nsteps - 1 else ' hidden', knotlib.svg_diagram(knot, built, i, scale=56))
        for i in range(nsteps))
    steps_html = ''.join(
        '<li><div class="step" data-i="%d" role="button" tabindex="0"><b>%d</b><span>%s</span></div></li>' % (i, i + 1, gloss(s['text'], up))
        for i, s in enumerate(knot['steps']))
    related = []
    for slug, note in k['related']:
        if slug and slug in by_slug:
            related.append('<li><a href="../%s/index.html">%s</a> <span>%s</span></li>' % (slug, E(by_slug[slug]['name']), E(note)))
        else:
            name, _, rest = note.partition(':')
            related.append('<li><span class="soon">%s</span> <span>%s</span></li>' % (E(name), E(rest.strip())) if rest else
                           '<li><span>%s</span></li>' % E(note))
    aka = ('<p class="aka">Also called %s</p>' % ', '.join(E(a) for a in k['aka'])) if k['aka'] else ''
    safety = ('<p class="safety" role="note">%s</p>' % E(SAFETY)) if SAFETY in k['cautions'] else ''
    cautions = [c for c in k['cautions'] if c != SAFETY]
    body = f'''
<article class="knot" data-slug="{k['slug']}">
  <div class="knot-head">
    <p class="eyebrow"><a href="{up}index.html#{k['chapter']}">{E(CHAPTERS[k['chapter']][0])}</a></p>
    <h1>{E(k['name'])}</h1>
    {aka}
    <p class="lede">{E(k['brief'])}</p>
    <div class="meta">{chips(k, up)}</div>
    <dl class="facts">
      <div><dt>Difficulty</dt><dd>{difficulty(k['difficulty'])}</dd></div>
      <div><dt>Security</dt><dd>{E(k['security'])}</dd></div>
      <div><dt>Untying</dt><dd>{E(k['untie'])}</dd></div>
    </dl>
  </div>

  <section class="bench" aria-label="Step-by-step tying">
    <div class="stage" id="stage">
      <div class="view3d" id="view3d"><p class="hint" id="hint">Drag to turn the knot. Scroll or pinch to zoom.</p></div>
      <div class="view2d" id="view2d" hidden>{diagrams}</div>
      <div class="tools">
        <button type="button" id="play" class="primary">Play</button>
        <button type="button" id="mirror" aria-pressed="false" title="Mirror image, for tying with the other hand">Mirror</button>
        <button type="button" id="reset">Reset view</button>
        <button type="button" id="flat" aria-pressed="false">Flat diagram</button>
      </div>
    </div>
    <div class="side">
      <div class="scrub">
        <label for="scrub">Step <output id="stepno">{nsteps}</output> of {nsteps}</label>
        <input id="scrub" type="range" min="0" max="{(nsteps - 1) * 100}" value="{(nsteps - 1) * 100}" step="1">
      </div>
      <ol class="steps" id="steps">{steps_html}</ol>
      <p class="keys">Arrow keys step through. Tags show whether the moving end passes <span class="tg-o">over</span> or <span class="tg-u">under</span>.</p>
    </div>
  </section>
  {safety}
  <div class="cols">
    <section><h2>Use it for</h2><ul>{''.join('<li>%s</li>' % E(u) for u in k['uses'])}</ul></section>
    <section><h2>Watch out</h2><ul>{''.join('<li>%s</li>' % E(c) for c in cautions)}</ul></section>
    <section><h2>Untying</h2><p>{E(k['untie_how'])}</p>
      <button type="button" class="learn" id="learn" aria-pressed="false">Mark as learned</button></section>
  </div>
  <section class="related"><h2>Related knots</h2><ul>{''.join(related)}</ul></section>
</article>
<script type="application/json" id="knot-data">{json.dumps(data, separators=(',', ':'))}</script>
'''
    scripts = ('<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>\n'
               '<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>\n'
               '<script src="{up}assets/bench.js"></script>')
    return page('knots/%s/index.html' % k['slug'], '%s | Knot Atlas' % k['name'],
                '%s: %s' % (k['name'], k['brief'][:140]), body, nav='knots', cls='p-knot', scripts=scripts)


def thumb(knot, built):
    return knotlib.svg_diagram(knot, built, None, scale=40, labels=False)


def index_page(items):
    cards = []
    for k, knot, built in items:
        cards.append(f'''<li class="card" data-ch="{k['chapter']}" data-acts="{' '.join(k['acts'])}" data-name="{E((k['name'] + ' ' + ' '.join(k['aka'])).lower())}">
  <a href="knots/{k['slug']}/index.html">
    <div class="thumb">{thumb(knot, built)}</div>
    <span class="eyebrow">{E(CHAPTERS[k['chapter']][0])}</span>
    <h3>{E(k['name'])}<span class="tick" aria-label="learned" hidden>✓</span></h3>
    <p>{E(k['brief'].split('. ')[0])}.</p>
    <span class="dots-line">{difficulty(k['difficulty'])}</span>
  </a></li>''')
    counts = {c: sum(1 for k, _, _ in items if k['chapter'] == c) for c in CHAPTERS}
    chap_btns = ''.join('<button type="button" data-ch="%s" aria-pressed="false" id="ch-%s">%s</button>' % (c, c, E(v[0]))
                        for c, v in CHAPTERS.items() if counts[c])
    act_opts = ''.join('<option>%s</option>' % a for a in ACTIVITIES)
    upcoming = ''.join('<li><b>%s</b> <span>%s</span></li>' % (E(v[0]), E(v[1])) for c, v in CHAPTERS.items() if not counts[c])
    body = f'''
<section class="hero">
  <p class="eyebrow">An interactive field guide</p>
  <h1>Knot Atlas</h1>
  <p class="lede">Every knot here is a 3D rope you can turn in your hand and tie one step at a time. The over and under tags come from the model itself, so they always agree with the drawing.</p>
  <p class="hero-links"><a class="btn" href="finder/index.html">Find a knot for a job</a> <a class="btn ghost" href="basics/index.html">Start with the basics</a></p>
  <p class="meta acts">Best knots for: {''.join('<a class="chip" href="for/%s/index.html">%s</a>' % (a.lower(), a) for a in ACTIVITIES if any(a in k['acts'] for k, _, _ in items))}</p>
</section>
<section class="catalogue" aria-labelledby="cat-h">
  <h2 id="cat-h" class="sr">All knots</h2>
  <div class="filterbar">
    <div class="chiprow" role="group" aria-label="Chapter"><button type="button" data-ch="all" aria-pressed="true" id="ch-all">All</button>{chap_btns}</div>
    <div class="fields">
      <label>Activity <select id="act"><option value="">Any</option>{act_opts}</select></label>
      <label>Search <input id="q" type="search" placeholder="Name or other name" autocomplete="off"></label>
    </div>
  </div>
  <p class="count" id="count" aria-live="polite">{len(items)} knots</p>
  <ul class="grid" id="grid">{''.join(cards)}</ul>
</section>
<section class="upcoming">
  <h2>Being drawn now</h2>
  <p>The guide grows chapter by chapter. Next come more stoppers, binding knots, bends, hitches and loops, then:</p>
  <ul>{upcoming}</ul>
</section>
'''
    return page('index.html', 'Knot Atlas: interactive 3D knot guide',
                'Learn knots step by step with 3D ropes you can turn, scrub and mirror. Stoppers, bends, hitches and loops for sailing, climbing, camping and home.',
                body, nav='knots', cls='p-index', scripts='<script src="{up}assets/site.js"></script>')


def finder_page(items):
    data = [{'slug': k['slug'], 'name': k['name'], 'jobs': k['jobs'], 'acts': k['acts'], 'difficulty': k['difficulty'],
             'brief': k['brief'].split('. ')[0] + '.', 'security': k['security'], 'untie': k['untie']}
            for k, _, _ in items]
    jobs = ''.join('<option value="%s">%s</option>' % (j, E(t)) for j, t in JOBS.items())
    acts = ''.join('<option>%s</option>' % a for a in ACTIVITIES)
    body = f'''
<section class="page-head">
  <p class="eyebrow">Knot finder</p>
  <h1>What does the rope have to do?</h1>
  <p class="lede">Pick the job and where you are. You get the best knots in this guide for it, easiest first, with what each one is good and bad at.</p>
</section>
<section class="finder">
  <form class="fq" id="fq">
    <label for="job">I need to</label>
    <select id="job">{jobs}</select>
    <label for="where">Setting</label>
    <select id="where"><option value="">Anywhere</option>{acts}</select>
    <label class="check"><input type="checkbox" id="undo"> It must be easy to untie afterwards</label>
  </form>
  <div class="answers" id="answers" aria-live="polite"></div>
</section>
<p class="note">Joining two ropes? Don’t use a Square Knot for that. It can spill apart under load.</p>
<script type="application/json" id="finder-data">{json.dumps(data)}</script>
'''
    return page('finder/index.html', 'Knot finder | Knot Atlas', 'Choose a knot by what the rope has to do: stop, join, attach, loop, grip or bind.',
                body, nav='finder', cls='p-finder', scripts='<script src="{up}assets/finder.js"></script>')


def about_page(n):
    body = f'''
<section class="page-head prose">
  <p class="eyebrow">About</p>
  <h1>How this guide is made</h1>
  <p class="lede">Knot Atlas teaches {n} knots so far, each one drawn from a 3D model of the rope rather than from photographs.</p>
</section>
<section class="prose">
  <h2>The rope models</h2>
  <p>Each knot is described as one or more ropes: a smooth centreline through a set of control points, with a rope thickness. Knots tied in the flat are described as a drawing plus a code that says, at each crossing, which strand goes over. Knots tied round a post, a ring or another rope are modelled directly in 3D.</p>
  <p>Before a knot is published a checker runs on the model. It confirms that no part of the rope passes through another part, through another rope, or through the post or ring, and that the number of crossings matches the knot’s code. The step-by-step view reveals the rope in the order you tie it, and the over and under tags are read from the model at each crossing the moving end makes.</p>
  <h2>What the drawings show</h2>
  <p>The models show knots loosely, so you can see the path of the rope. A real knot drawn tight looks more compact. Mirror shows the mirror-image knot, which is the same knot tied with the other hand. Every flat diagram is a projection of the same model.</p>
  <h2>Safety</h2>
  <p>{E(SAFETY)} Nothing on this site replaces training, manufacturer instructions or local rules for climbing, rescue, lifting or boating.</p>
  <h2>Credits</h2>
  <p>3D rendering uses <a href="https://threejs.org/">three.js</a>. Type is set in Barlow Condensed and IBM Plex. Knot names are the common names used by sailors, climbers and anglers; where a knot has several names, the others are listed under its title.</p>
</section>
'''
    return page('about/index.html', 'About | Knot Atlas', 'How Knot Atlas models knots, checks them, and what the drawings show.',
                body, nav='about', cls='p-about')


ACT_INTRO = {
    'Sailing': 'Boats run on a handful of knots: stoppers for sheet ends, hitches for fenders and moorings, a loop for almost everything else. These are the ones worth knowing without thinking.',
    'Climbing': 'Climbing knots hold people, so they are chosen for security and for how easy they are to check by eye. Learn them from an instructor; use this page to revise.',
    'Camping': 'Tarps, guy lines, bundles and washing lines. Knots that are quick to tie with cold hands and quick to undo when you pack up.',
    'Fishing': 'Line is thin and slippery, so fishing knots use extra turns for grip. Wet the line before you pull a knot tight.',
    'Household': 'Parcels, bags, washing lines, tie-downs and shoelaces. The everyday knots that save string and temper.',
    'Gardening': 'Tying plants to stakes, bundling canes and fixing nets. Knots that grip without slipping and are easy to cut away.',
    'Horses': 'Tying to rings and rails where a quick release matters. Follow your yard\u2019s rules for tying animals.',
    'Gifts': 'Decorative and finishing knots for ribbons, cords and handmade presents.',
}


def activity_pages(items):
    paths = []
    for act in ACTIVITIES:
        ks = [(k, n, b) for k, n, b in items if act in k['acts']]
        if not ks:
            continue
        ks.sort(key=lambda t: (t[0]['difficulty'], t[0]['name']))
        cards = ''.join('''<li class="card"><a href="../../knots/%s/index.html"><div class="thumb">%s</div>
  <span class="eyebrow">%s</span><h3>%s</h3><p>%s</p><span class="dots-line">%s</span></a></li>''' % (
            k['slug'], thumb(n, b), E(CHAPTERS[k['chapter']][0]), E(k['name']), E(k['brief'].split('. ')[0] + '.'),
            difficulty(k['difficulty'])) for k, n, b in ks)
        others = ''.join('<a class="chip" href="../%s/index.html">%s</a>' % (a.lower(), a) for a in ACTIVITIES if a != act and any(a in k['acts'] for k, _, _ in items))
        body = f'''
<section class="page-head"><p class="eyebrow">Best knots for</p><h1>{E(act)}</h1>
<p class="lede">{E(ACT_INTRO[act])}</p></section>
<ul class="grid">{cards}</ul>
<section class="related"><h2>Other activities</h2><div class="meta">{others}</div></section>'''
        paths.append(page('for/%s/index.html' % act.lower(), '%s knots | Knot Atlas' % act,
                          'The most useful knots for %s, easiest first.' % act.lower(), body, nav='knots', cls='p-for'))
    return paths


def write_meta(paths):
    urls = ''.join('<url><loc>%s%s</loc></url>' % (SITE, p[:-len('index.html')] if p.endswith('index.html') else p) for p in paths)
    open(os.path.join(ROOT, 'sitemap.xml'), 'w').write(
        '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>\n' % urls)
    open(os.path.join(ROOT, 'robots.txt'), 'w').write('User-agent: *\nAllow: /\nSitemap: %ssitemap.xml\n' % SITE)
    lines = ['# Knot Atlas', '', 'Interactive 3D guide to tying knots.', '', '## Knots', '']
    for k in KNOTS:
        lines.append('- [%s](%sknots/%s/): %s' % (k['name'], SITE, k['slug'], k['brief'].split('. ')[0]))
    lines += ['', '## Basics', ''] + ['- [%s](%sbasics/%s/)' % (b['title'], SITE, b['slug']) for b in basics.PAGES]
    open(os.path.join(ROOT, 'llms.txt'), 'w').write('\n'.join(lines) + '\n')


def main():
    check_only = '--check' in sys.argv
    items, bad = [], False
    for k in KNOTS:
        knot, built = build_knot(k)
        probs = list(built['problems'])
        kt = ''
        if k.get('expect'):
            V = knotlib.jones(built['ropes'], knot.get('closure', [(0, 1)]))
            if knotlib.knot_type_ok(V, k['expect']):
                kt = 'type %s ok' % k['expect']
            else:
                probs.append('knot type is not %s (Jones %s)' % (k['expect'], knotlib.jones_str(V)))
        status = 'ok' if not probs else '; '.join(probs)
        print('%-34s %3d crossings  %s %s' % (k['slug'], len(built['crossings']), status, kt))
        bad = bad or bool(probs)
        items.append((k, knot, built))
    if check_only:
        sys.exit(1 if bad else 0)
    by_slug = {k['slug']: k for k in KNOTS}
    paths = [index_page(items), finder_page(items), about_page(len(items))]
    for k, knot, built in items:
        paths.append(knot_page(k, knot, built, by_slug))
    paths += basics.build(page)
    paths += activity_pages(items)
    write_meta(paths)
    print('wrote %d pages' % len(paths))
    if bad:
        print('WARNING: geometry problems above')


if __name__ == '__main__':
    main()
