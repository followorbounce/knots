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

## 2026-10-13: Wave 2 (20 more knots, 32 total)
- Knot-type check: build closes each rope through the outside of the drawing and
  computes the Jones polynomial; knots with an `expect` in knots.py must match
  (3_1, 4_1, 5_1, 6_1, 9_1, square, granny, unknot for slipped knots). This found
  that the wave-1 Square Knot model actually closed to an unknot (fixed, code uouuou).
- Engine: `ensure_gaps` (keeps over/under, lifts crossings apart) and `repel`
  (small push-apart for near misses) run before the checker.
- Helpers in geometry.py: `_coil_knot` (multiple overhands), `_slip` (slipped
  finishes through the last tuck), `_doubled` (knots on a bight), `_fisher_half`,
  `_ring_hitch` (turn/round turn + half hitches, buntline when toward_ring).
- New knots: slipped overhand, double overhand, multiple overhand, slipped
  figure-eight, stevedore, granny, thief, slipped square, bow, overhand loop,
  threaded figure-eight loop, Englishman's loop, double Englishman's loop, double
  overhand noose, cow hitch, round turn bowline, half hitch, two half hitches,
  buntline hitch, timber hitch.
- Site: best-for activity pages (/for/<activity>/), glossary links in step text,
  sRGB colour fix in the bench.

## Still to do from the stopper/binding/hitch/loop chapters
Sink stopper, true lover's knot, sailor's cross, surgeon's knot (and with second
tuck), turquoise turtle, packer's knot, boa knot, pedigree cow hitch, cow hitch
with toggle, sheepshank, sheepshank man o' war, marlinspike hitch, highwayman's
hitch, waggoner's hitch, icicle hitch, Bachmann, Klemheist, Italian hitch (and
reversed), mirrored rolling hitch, alpine butterfly, bowline with stopper,
bowline on the bight, Portuguese bowline, Spanish bowline, angler's loop,
single figure-eight loop on the bight. Most need either a new 3D construction
(carabiner, toggle, hook) or a careful flat drawing checked against the reference.

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
