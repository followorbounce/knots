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
Owner decision 2026-10-14: the 12 knots in `REDRAW` stay as they are, with their notice; no redraw planned.
Cow Hitch and Pedigree Cow Hitch are fixed. Further work only on request.

## Snippets
Tag dump per step (check captions):
    python3 -c "import build,knotlib;from knots import KNOTS
    for k in KNOTS:
        n,b=build.build_knot(k);print(k['slug'],[''.join('O' if t['over'] else 'U' for t in knotlib.step_tags(n,b,i)) for i in range(len(n['steps']))])"

## 2026-10-14: Cow Hitch rebuilt from the reference picture, crossing by crossing (owner: still wrong, twice)
Reference: _todo/Cow-Hitch-Lark's-Head-Knot-Instructions.jpg, viewed from the side of the two loops.
Traced: the standing leg hangs BEHIND the rail (the rail hides it); the rope climbs the back, comes over the
top towards the viewer, down the front, under the rail and back; the crossing piece (bight) passes BEHIND the
standing leg; the other side mirrors it and comes down the back between the rail and the bight. So:
bight on the back, outside both legs; each leg makes one full turn going UP the bight's face first.
- The 10-13 "topology corrected" model wound each leg the other way (under the rail first): its bight can
  ride up and free the legs, so it is not a hitch.
- The 7340355 model (restored earlier today) had the right structure but was shown from the bight's side,
  so it did not look like the picture.
New `cow_hitch()` is drawn explicitly round the rail (`_ring(phi, r)`, 0 = top, 90 = front) and shown from
the loops side, tightened as in the picture's last step. Pedigree Cow Hitch: legs spaced wider so the tuck
goes up between the two legs, under the bight, and down outside it. Rendered from front, back, below and
above (canvas capture with the coordinates rotated) and compared with the picture; checker clean.
Both windings have zero net turns round the rail, so no automatic check can tell them apart.

## 2026-10-13: Cow Hitch redrawn (owner report: "just not a knot")
The old model was topologically a lark's head, but the bight hung loose below the rail
and each leg vanished into the rail's underside, so the picture read as a U draped over
a bar. New `cow_hitch()`: each leg runs up the front of the rail under the bight, one
full turn (over the top, down the back, under, up the front outside the leg), and the
bight lies flat across the front over both legs, the standard view of the hitch. Net winding
round the rail is 0, as for a real cow hitch. Pedigree Cow Hitch rebuilt on it (tuck
goes up between the legs and the bight, then down in front). Captions updated.

## 2026-10-13: Visual audit of all 75 (owner: "half of the knots are not knots")
Rendered every final 3D view and reviewed it against how the knot is actually tied.
Clearance + Jones checks do not catch "does not read as the knot". 14 failed and are
listed in `knots.REDRAW`: their pages carry a "Drawing being redrawn" notice and they
are left out of the homepage feed until each is redrawn and checked against a reference
picture. Minor: the eye of Figure-Eight Loop / Threaded Figure-Eight Loop is angular.
New rule: a knot ships only after its final render has been compared with a reference
picture of the tied knot, not only after the checker passes.
- Redrawn and released: Half Hitch (looser hitch, clean exit), Square Lashing (poles
  1:7 to rope like real spars; turns go over the crossbar and straight back between the
  poles; frapping turns sit in the gap round the bundle).

## 2026-10-13: Cow Hitch topology corrected (owner: "the physics/topology is still wrong")
The previous redraw wound each side the wrong way: the leg ran up the face of the rail
under the bight and then over the top, which is an upside-down cow hitch with its legs
folded back, not a cow hitch. Both versions have zero net winding round the rail, so the
winding check could not tell them apart. Correct structure (tying with a bight, legs
pulled through): from each leg upward the rope goes under the rail to the front, up the
front, over the top and down the back to the bight; the bight sits just under the rail at
the back, outside both legs. Seen from the front: two loops over the rail and the legs
between them, as in the owner's reference picture. Pedigree Cow Hitch rebuilt on it.

## 2026-10-16 — Multiple overhand redrawn
- Owner: in step 5 the line must go through the initial loop; the old barrel drawing (`_coil_knot(4)`: tail run back inside the coils, out beside the U-turn) closed to 9_1 but did not read as a knot. New `_loop_wrap(n)` in geometry.py draws it as tied: a loop closed under the standing part, the end brought up behind the loop and wrapped n times round its right side, every wrap through the loop. Jones-checked for n=1..4 (3_1, 5_1, 7_1, 9_1); the first draft had the loop crossing over the standing part and came out one twist short (n=4 gave 7_1), fixed by taking the end under. Steps rewritten to match (loop / tuck / coil / end). Full build: all knots ok, no warnings. Double overhand still uses the barrel drawing.

## 2026-10-21 — Checker upgrades (before the new-knots Wave 1)
Owner approved Wave 1 of the new-knots proposal (`/home/none/git/_todo/knots-new-knots-proposal-2026-10.html`):
cleat hitch, trucker's hitch, taut-line hitch, anchor bend, alpine butterfly, zeppelin bend,
figure-nine stopper, Ashley stopper, uni knot, autoblock. Checker first:
- `KNOWN['5_2']` added (needed for the figure-nine).
- `tests/check_jones.py`, run by `build.py` before anything else: every KNOWN entry
  (3_1, 4_1, 5_1, 5_2, 6_1, 7_1, 9_1) recomputed from its PD code with an independent
  bracket routine; 8_18 from the closed braid (s1 s2^-1)^4 (a PD code recalled from memory
  for 8_18 was wrong, det 37, and was not used); `jones_loops` checked on torus (3,2),
  (5,2), the figure-eight curve, Hopf link and unlink; the closure rule on open arcs.
- `knotlib.close_above_below` / `jones_loops` / `link_pair` / `rope_alone`: links of
  several ropes under one fixed closure rule (rope 0 closed above everything, rope 1
  below), so link values do not depend on how the closing arcs are drawn. Crossings
  that land exactly on a polyline vertex are de-duplicated in the new code
  (found with a braid sampled on its crossings; `find_crossings` itself unchanged).
- `expect_link` pins on the 7 two-rope knots (square, granny, sheet bend, fisherman's,
  water, flat overhand, carrick). Square ropes are unlinked (lk 0), granny lk -3:
  the link test separates them, the per-rope test cannot.
- Closure validity: a whole closure with half powers of t is reported as invalid.
  The "other pairing" of ends in two-rope knots is invalid in every bend tried,
  so it is not used.
- `tools/invariants.py <slug>`: per-rope types (old and fixed closure), link, closure.
- Per-rope checking (`expect_each`) already existed; the proposal page listed it as new.
- Checked: all 75 knots unchanged vs the baseline run; mutation test (square pinned
  with granny's link, overhand expected 5_2) fails the build as it should.

## 2026-10-28 — Reach plan F3: page weight
Site total 39.2 MB → 9.8 MB. Front page 6.15 MB → 0.05 MB; "best knots for" pages 0.9–2.8 MB → ~0.02 MB; largest knot page (square lashing) 1.24 → 0.50 MB. Thumbnails are now lazy-loaded files in `assets/thumbs/` (75); step drawings use the compact path encoding (pixel-identical). Stretch merging measured and left off (see CLAUDE.md). Share cards use the thumbnail files. Not yet pushed.
