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

## 2026-10-13: Wave 5 (5 more, 58 total) + homepage widget
- Splices built with a cylinder-weave engine (`_cyl_weave`): strands drawn on an
  unrolled rope surface, crossings found on an annulus picture of the cylinder,
  tucked stretches go over-under-over the lay strands (lay strands lift where a
  tuck goes under). Back Splice (crown + 3 rounds), Eye Splice (laid strands follow
  a curved centreline with a rotation-minimising frame), Short Splice (two ropes
  married, 60 tuck crossings, all resolved).
- Whippings: knots can set their own cord radius (`'r': TW`), and poles can be
  `'rope': True` (rope-textured objects). Common Whipping, Flat Seizing.
- `feed/index.json` + `feed/<slug>.json`: compact centrelines + steps for the
  "Knot of the day" widget on the followorbounce.github.io homepage
  (engine/knot-of-day.* there). Keep the feed format stable: slug, name, chapter,
  brief, difficulty, acts, r, ropes [{c, p}], objects, steps [{t, v}].

## 2026-10-13: Backlog pass (17 more, 75 total)
Shipped, each passing clearance; knot type checked by Jones where it closes:
Marlinspike Hitch (unknot), Mirrored Rolling Hitch, Pedigree Cow Hitch, Cow Hitch
with Toggle, Bowline with Stopper, Double Sheet Bend (3D sheet bend, 2 turns),
Sheepshank (unknot), Klemheist, Italian Hitch, Blood Dropper Loop, Four-Strand
Round Sennit, Eight-Strand Square Sennit (`_tube_weave`), Surgeon's Knot
(KNOWN 'surgeon' = 5_1 # mirror 3_1, code 'uouuuuouou'), Surgeon's Knot with
Second Tuck ('surgeon2' = 5_1 # mirror 5_1, code 'uouooouuuuouou', tw_top=1),
Highwayman's Hitch (unknot), Palomar Knot (doubled overhand above a hook eye,
bight round the shank), Bimini Twist (relax False; 8 twists, coil back, half hitch).
Codes for the surgeon's knots came from an exhaustive search over the twisted
square-knot layout (`_surgeon_layout`), keeping codes that close to the right type.

## Held back (not verified; do not publish without a checked model)
- Hunter's Bend: first model closed to unknots per rope, not trefoils. Removed.
- Bachmann Knot: model exists (`bachmann_knot`, marked NOT PUBLISHED); wraps run
  through the carabiner spine and tangle after relaxation.
- Structure not yet modelled with confidence: Tucked Sheet Bend, Ashley's Bend,
  Rope Yarn Knot, Lanyard Knot, Spanish / Portuguese bowline, bowline on the bight,
  single figure-eight loop on the bight, alpine butterfly, angler's loop, true
  lover's knot, sailor's cross, turquoise turtle, boa, sink stopper, packer's knot,
  sheepshank man o' war, waggoner's hitch, icicle hitch, reversed Italian hitch
  (mentioned in the Italian hitch text), Snelling a Hook.
- Decorative/many-strand: Matthew Walker, Manrope and Diamond knots; Ocean-Braid
  and Oval mats; Chain Sennit; Round Crown, Six-Strand Round Crowning and Square
  Crown sennits; nets; Diagonal Lashing; jury mast knot.
- Whipping/splice work: French, Sailmaker's and Palm-and-Needle whippings;
  Tapering a Splice; Stitch and Seize.

## Known limits
- Final "tighten" steps show the loose, dressed model; there is no tightened shape yet.
- Prusik and Double Fisherman's steps describe structure with tags switched off
  (wraps give too many tags to read).
- No in-browser authoring tool yet; models are authored in Python and checked with
  `tools/preview.py`.

## Next
Work through "Held back" above, one verified model at a time.

## Snippets
Tag dump per step (check captions):
    python3 -c "import build,knotlib;from knots import KNOTS
    for k in KNOTS:
        n,b=build.build_knot(k);print(k['slug'],[''.join('O' if t['over'] else 'U' for t in knotlib.step_tags(n,b,i)) for i in range(len(n['steps']))])"

## 2026-10-13: Cow Hitch redrawn (owner report: "just not a knot")
The old model was topologically a lark's head, but the bight hung loose below the rail
and each leg vanished into the rail's underside, so the picture read as a U draped over
a bar. New `cow_hitch()`: each leg runs up the front of the rail under the bight, one
full turn (over the top, down the back, under, up the front outside the leg), and the
bight lies flat across the front over both legs, the standard view of the hitch. Net winding
round the rail is 0, as for a real cow hitch. Pedigree Cow Hitch rebuilt on it (tuck
goes up between the legs and the bight, then down in front). Captions updated.
