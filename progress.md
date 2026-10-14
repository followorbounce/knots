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

## 2026-10-13: Wave 3 (8 more knots, 40 total)
- Bends: Fisherman's Knot, Water Knot, Blood Knot, Flat Overhand Bend.
- Lashings (new chapter): Sheer Lashing, Square Lashing.
- Fishing: Clinch Knot, Improved Clinch Knot, on a modelled hook (eye ring,
  metal shank, `arc` object for the bend).
- Check: `expect_each` in knots.py tests each rope on its own (e.g. each half of
  a fisherman's knot is an overhand, each blood-knot line alone is unknotted).
- Engine: `push_out` keeps relaxed rope out of poles; knots with poles can use
  `'relax': 'gaps'` (crossing lift only) when their raw geometry is clean.

## 2026-10-13: Wave 4 (13 more, 53 total)
- Turk's head generator: annulus drawing r = r0 + a cos(B t / L), t in [0, 2 pi L],
  forced alternating, rolled onto a pole. Validated: (2,3) = trefoil, (3,2) =
  figure-eight, (2,5) = 5_1, (3,4) = 8_18 exactly; crossing count B(L-1).
- New: Turk's heads 3L4B, 4L5B, 5L4B; Carrick Bend (3L4B mat cut at two outer
  bights, rejoins to 8_18, each rope alone unknotted); Carrick Mat (doubled);
  Monkey's Fist (three woven bands, transitions routed over the outside);
  Crown and Wall knots on a laid 3-strand rope; flat braids of 3-7 strands.
- Knots wrapped round poles or balls use `'wrapped': True` (3D clearance only,
  projected crossing gaps ignored) and `'relax': 'repel'`. Per-knot camera
  elevation via `view: {elev}`. Steps can reveal per-strand fractions (`fl`).
- Build is slow (~4 min): flat braid 7 and multiple overhand dominate.

## Still to do from wave 4
Matthew Walker, Manrope and Diamond knots; Ocean-Braid and Oval mats; Chain
Sennit; Four-Strand Round, Eight-Strand Square, Round Crown, Six-Strand Round
Crowning and Square Crown sennits.

## Still to do from wave 3
Carrick Bend (build from the 3-lead 4-bight Turk's head generator in wave 4),
Hunter's Bend, Ashley's Bend, Double and Tucked Sheet Bends, Rope Yarn Knot,
Lanyard Knot, Diagonal Lashing, Palomar Knot (first model was ambiguous at its
crossings and was dropped), Snelling a Hook, Blood Dropper Loop, Bimini Twist,
nets.

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
