# Progress

## 2026-10-13: Wave 1 shipped (12 knots)
- Engine (`knotlib.py`): Catmull-Rom ropes, crossing-code over/under, clearance
  checker, SVG step diagrams, JSON export for the 3D bench.
- 12 knots: Overhand, Figure-Eight, Square, Clove Hitch, Constrictor, Sheet Bend,
  Double Fisherman's, Rolling Hitch, Round Turn & Two Half Hitches, Prusik,
  Bowline, Figure-Eight Loop. All pass the checker; step tags verified against captions.
- Pages: catalogue (chapter/activity/search filters, learned ticks), knot pages
  (3D bench: steps, scrubber, play, mirror, reset, flat diagram, keyboard; uses,
  cautions, untying, related, mark-as-learned), finder, 6 basics pages
  (construction tabs, materials table, care checklist, coiling, terms with
  interactive rope anatomy + turn/round-turn figure, technique), about.

## Known limits
- Final "tighten" steps show the loose, dressed model; there is no tightened shape yet.
- Prusik and Double Fisherman's steps describe structure with tags switched off
  (wraps give too many tags to read).
- No in-browser authoring tool yet; models are authored in Python and checked with
  `tools/preview.py`.

## Next (Wave 2)
Rest of stoppers, binding knots, hitches and loops (~60), then bends/lashings/
fishing knots (wave 3), generated Turk's heads/braids/sennits (wave 4),
splices and whippings as strand diagrams (wave 5).

## Snippets
Tag dump per step (check captions):
    python3 -c "import build,knotlib;from knots import KNOTS
    for k in KNOTS:
        n,b=build.build_knot(k);print(k['slug'],[''.join('O' if t['over'] else 'U' for t in knotlib.step_tags(n,b,i)) for i in range(len(n['steps']))])"
