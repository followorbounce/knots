# Knot Atlas

An interactive field guide to tying knots. Every knot is a 3D rope model you can
turn, scrub through step by step, mirror for the other hand, or view as a flat
diagram. Over/under tags are read from the model, so they always match the drawing.

Live: https://followorbounce.github.io/knots/

## Build

    python3 build.py           # regenerate the site (needs numpy)
    python3 build.py --check   # run the geometry checker only

Static output: `index.html`, `knots/`, `basics/`, `finder/`, `about/`, `sitemap.xml`,
`robots.txt`, `llms.txt`. Edit the sources, not the output:

| File | What it holds |
|---|---|
| `knots.py` | Text for every knot: brief, uses, cautions, untying, steps |
| `geometry.py` | Rope models (control points, objects, step marks) |
| `knotlib.py` | Engine: spline, over/under resolution, checker, SVG, export |
| `basics.py` | The six primer pages |
| `assets/bench.js` | three.js tying bench on knot pages |
| `tools/preview.py` | Dev preview: renders one model to PNG with numbered crossings |
