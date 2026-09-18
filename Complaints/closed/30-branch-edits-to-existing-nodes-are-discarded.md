# `treetool.py merge` silently discards every branch edit to an existing node

**Type:** Tooling / data integrity
**Priority:** High. It has probably already eaten work.

## What happens

`data/branches/*.json` is the documented authoring surface for the tech tree.
`data/tech_tree.json` is generated from it by `python3 sim/treetool.py merge`.
`CONTRACT_V2.md` tells branch authors to edit their branch file. Every
instruction in this repository says the same.

That only works for a node id that does not already exist. **For an existing
node, the branch file is decorative.** Editing it and re-merging changes
nothing, and nothing says so.

Demonstrated, not inferred:

```
branch file said           cap = 424242.0
tech_tree.json after merge, cap = 1500.0
```

The value was set in `data/branches/18_chemicals.json`, `merge` was run, and
the merged tree came back with the old number.

## Why

`cmd_merge` in `sim/treetool.py` seeds `nodes` from the CURRENT
`data/tech_tree.json` first, then walks the branch files adding what is
missing. A branch node whose id is already present is skipped with

    <file>: duplicate id <id>, keeping the first

which is emitted among roughly 3,200 other lines of merge output. The last
five are what a human reads, so in practice it is silent.

## Why this matters more than it looks

**It has probably already eaten work.** Anyone who has edited a branch file to
correct an existing node's cost, prerequisites or materials over the life of
this project got no error, no warning they would see, and no effect. The
branch files and the tree can therefore disagree, and the tree wins. Nobody
has checked how far apart they have drifted.

This was found twice in one day by accident, both times by someone assuming
the documented workflow worked:

1. A production recipe added to `mat_copper` in `01_materials.json` vanished
   on merge. That is what pushed the production data into its own directory
   with its own loader, which turned out well but for the wrong reason.
2. An agent fixing `Complaints/28` edited two branch files, re-merged,
   and found the tree unchanged. It had to edit `tech_tree.json` directly and
   flagged the discrepancy.

A third consequence, recorded in `mods/TASKS.md` item 1: this is the single
blocker for a mod ever overriding a base node. A mod that redefines anything
would appear to install and do nothing.

## Also found

`freedman_staff` has `"_src": "core"` and appears in **no** branch file at
all. It predates the branches split. So "edit the branch file" is not merely
ineffective for some nodes, it is impossible - there is nothing to edit. How
many core-only nodes exist has not been counted.

## Expected behavior

A branch file is the source; the tree is generated. Either:

- a branch node overwrites the merged node, and the merge reports how many it
  updated, or
- an id defined in both is an ERROR that names both sides, which is what
  `sim/validate_production.py` already does for `data/production/` and is why
  that directory does not have this problem.

The second is probably right for the base game and the first for mods, which
is the same distinction `mods/TASKS.md` item 3 arrives at from the other
direction: an override should have to be explicit.

Whichever is chosen, the merge must say what it did. A tool that rewrites 2.8
megabytes of game data and reports the interesting part on line 3,205 of its
own output is not reporting it.

## Before fixing it

Count the drift first. Compare every branch node against its merged twin and
report the differences: that tells you how much silently-discarded work is
sitting in the branch files right now, and whether the fix will change the
game's behaviour when it starts taking effect. Do that before changing the
merge, not after - a fix that silently applies years of accumulated
divergence in one commit is its own kind of accident.

---

## The drift, counted (this is the answer to "Before fixing it", above)

Done. The naive comparison - re-apply `cmd_merge`'s own transformation to
each branch node and diff against its merged twin - reproduces the ~99.4%
disagreement and is the trap this section warned about, because `cmd_repair`
and `cmd_apply_caps` are a THIRD transformation stage that writes straight
to `tech_tree.json` and never round-trips to branches by design. They append
inferred capability prerequisites, fill empty `kb` with a module doc path,
default `gov`/`sus` when both are zero, and raise `yrs` floors.

Modelling all three stages splits the 2,719 comparable shared nodes:

```
(a)  explained by merge normalisation alone                    45   1.7%
(b)  explained once repair/apply-caps' append-only rules count 704  25.9%
(c)  STILL UNEXPLAINED - discarded branch edits or stale tree 1970  72.4%
```

Per field, for the 1,970:

```
up   1152     kb   829     rev  246     mat  171     lab  155
ph    136     cap  121     pre   85     conf  19     yrs   14
```

**`up` is not noise.** 1,074 of the 1,152 are "branch has a nonzero value,
the tree has 0", and they cluster in the `_deep.json` files - textiles 151,
medicine 122, manufacturing 117, science-method 99, chemistry 86, materials
85. That is the signature of a deliberate pass that added upkeep costs
across whole branch files and has been silently discarded on every merge
since. The `kb` residual is mostly the reverse: branches where a stale doc
anchor was REMOVED and the tree still carries it.

One consequence is already visible in the game. `cap_power_human` was
renamed to `cap_power_muscle` in the branches. Every tree node that
referenced the old id is frozen on it, because the rename never propagated -
and `cap_power_human` is itself one of the 144 orphans, so its definition is
gone from the branch file while the tree's stale copy survives.

## Decision: stages 3 and 4 are on hold, deliberately

Flipping the merge to make branches authoritative would apply roughly a
thousand upkeep changes in a single commit, sight unseen. That is exactly
the accident this complaint's own "Before fixing it" section was written to
prevent, and finding the number does not make it safe - it makes it
measurable.

What has to happen first: read a sample of the `_deep.json` `up` values
against their tree counterparts for AUTHOR INTENT, not structural
correctness. "The branch file has a number and the tree has zero" does not
establish which one somebody meant. Until that is done the tree stays
authoritative, because the devil we have measured beats the one we have not.

## What WAS done, because it is provably inert

`data/branches/00_core.json` now holds the 144 nodes that had no branch
source at all, backfilled verbatim minus three tool-internal bookkeeping
fields (`_src`, `_total_cost`, `kb_level`). 133 predate the branches split,
8 are surviving ids whose own definition has since vanished from the file
that once held them, and 3 are goal checkpoints carrying a `win_condition`
that `sim/engine/data.py` reads directly. Every node in the game now has a
branch source, so the documented workflow is at least POSSIBLE for all of
them - it is still ineffective for existing nodes until stage 3.

Inert under the unchanged merge, and checked rather than argued: every one
of the 144 ids is already seeded from the tree, so each hits the existing
"duplicate id, keeping the first" path. Running the real merge with the file
present produces a byte-identical `data/tech_tree.json`.

The 243 branch-only nodes were investigated and deliberately NOT added. All
243 are ids that `meta.merged_duplicate_ids` already retired into a
surviving id. Adding them would have resurrected retired duplicates, which
is the other accident this complaint warned about.

## One more collision, for whoever does stage 3

`lnd_whippletree` is defined in BOTH `data/branches/14_land_transport.json`
(cap=150, ph=50, conf=B) and `data/branches/55_realism_part02.json`
(cap=200, ph=80, conf=C), with different numbers. Today the merge keeps
whichever it reads first and says so on line 3,205. Under the "an id in two
files is an ERROR naming both sides" rule this section proposes, that is the
first thing it would catch.

---

## Stage 3 and the collision rule: done

`cmd_merge` now does both things this section asked for.

**Existing-node edits take effect.** A branch node whose id the tree already
carries now overwrites that node, FIELD BY FIELD, rather than being skipped.
It is a field-level overlay (`{**tree_node, **branch_node}`), not a wholesale
replace, for a reason discovered while building this: the tree carries keys
no branch schema has ever had a slot for - `kind`, `kb_level`, `_total_cost`,
`_internal` - written straight onto `tech_tree.json` by `judge`/`repair`/
`apply-caps`, which read and rewrite the tree directly and were never meant
to round-trip through branches. A wholesale replace was the first design
tried; measured against the real tree it erased `kind` on 2,695 nodes,
`kb_level` on 1,990 and `_total_cost` on 2,207 - entirely as a side effect of
fixing something else. The field-level overlay leaves every one of those
alone unless a branch file explicitly sets it, exactly as before this fix,
while a genuinely branch-authored field (`cap`, `ph`, `pre`, `mat`, `lab`,
`up`, `note`, `kb`, ...) now updates when its branch source does. The merge
summary now reports `added` and `updated` separately.

**The collision rule is implemented as proposed, option 2.** An id defined by
two different branch files (or twice in one file) in the same run is now an
ERROR naming both sides, and the merge REFUSES TO WRITE at all rather than
guess a winner - guessing is the exact silent decision that caused this
complaint. `sim/tests/test_branch_merge_authority.py` pins this, plus the
field-level-overlay behaviour, plus that a `meta.merged_duplicate_ids`-retired
id in two files is still just the existing "was merged into X, skipping"
warning, not a new collision to referee.

**`lnd_whippletree` turned out to already be resolved, differently than
expected.** Re-checking before touching anything (as the top of this file
asks): `meta.merged_duplicate_ids` already contains `"lnd_whippletree":
"tl_whippletree"` in the currently committed tree - added by other work
sometime after this section was written, unrelated to this fix. Both branch
definitions were therefore ALREADY hitting the "was merged into ..., skipping"
path on every merge, never the "duplicate id" path this section describes;
the collision this section demonstrates no longer occurs in the real corpus
today. What's left was housekeeping, not a decision: both definitions were
permanently dead (the id is retired project-wide, same as the 243 
branch-only retired ids this file already declined to resurrect), so both
were deleted from `14_land_transport.json` and `55_realism_part02.json`.
Checked, not argued: a merge dry-run before and after the deletion produces
byte-identical output - same node count, same ids, `lnd_whippletree` itself
unchanged (it is a zombie node with no active branch source at all; its tree
copy is what a reader still sees; that is a separate, pre-existing oddity -
a retired id's NODE isn't deleted from the tree by retirement, only its
incoming prerequisite edges are redirected - and is not this complaint's job
to fix).

**The full 2,864-node corpus was deliberately NOT re-merged for real.**
`python3 sim/treetool.py merge --dry-run` against the live tree and branches
now applies the fix in memory; comparing that result field-by-field against
the committed tree shows 2,834 of 2,864 nodes (99%) would change, dominated
by `kb` (2,605 nodes - mostly repair's module-level doc-link fallback,
restorable by re-running `repair` afterward, not lost), `pre` (1,204),
`up` (1,152, matching this file's own earlier drift count almost exactly),
`traits` (853), `note` (310, mostly repair's `[AUDIT: ...]` markers, same
restorable case as `kb`). This is the ~1,970-field drift this file already
measured and already decided to hold, now simply confirmed to still be
present at close to the same size, PLUS it surfaced three cycles in raw
branch `pre` data that the broken merge had been silently containing for
years (`mat_bulk_steel`, `cap_gas_o2h2` and `tl_electric_starter` each list
themselves as their own prerequisite; `sim/treetool.py`'s existing
cycle-breaker still catches these safely, they are noted here as a newly
visible authoring defect, not something this fix attempts to correct).
Applying this for real is still the "read a sample for AUTHOR INTENT" work
this file's own "Decision" section called for and never did - the mechanism
being correct is not the same thing as the backlog being reviewed - and
running the full `merge` → `repair` → `apply-caps` pipeline together, not
`merge` alone, is also part of doing that properly (running `merge` alone
against production and stopping there would look like data loss in `kb`,
`note` and `pre` until `repair` is re-run). `data/tech_tree.json` was left
byte-for-byte as committed by this work; only `sim/treetool.py` and the two
branch files with the resolved collision were changed.

---

## Done for real: regenerated, after moving the real work out of the tree first

The mechanism above was correct and untouched (`sim/treetool.py` needed no
further changes). What was still owed was this file's own repeated warning:
"the tree stays authoritative" only meant something *while nobody had
checked what was sitting in the tree and nowhere else*. That check is done
now, and this section is the record of it.

**Method.** `merge --dry-run` against the live tree and branches was
diffed field by field, not just counted. To separate "branches finally
applying" from "the tree quietly diverging from branches", every branch fix
found along the way was applied to a SCRATCH copy of the branches, the full
`merge` -> `repair` -> `apply-caps` pipeline was re-run against that scratch
copy, and the result was diffed against the real committed tree again. Repeat
until the only remaining differences are understood. That loop is what
turned "2,834 of 2,864 nodes would change" into a short, explainable list.

**What was REAL WORK sitting only in the tree, now moved into branches:**

- `traits` on 853 nodes - present in the tree, absent from every branch file.
  Once restored, `repair`'s `SOCIAL-FLAT` default-application stopped
  double-guessing `gov`/`sus` for those nodes, which is why the next two
  items exist.
- `gov`/`sus` scalars, hand-set (matching `repair`'s own category defaults,
  which is HOW they got their number in the first place, but no longer
  reproducible once `traits` was correct) on around 290 nodes.
- `kb` recipe-level doc anchors (e.g. `76_farming_food_deep.md#ag2_
  adulteration_law`) on 754 nodes - real, checked-against-`knowledge/`
  documentation links that existed only in the tree; branches had nothing,
  so `repair`'s generic module-level fallback was quietly standing in for
  real content on every one of them.
- `note` prose on 292 nodes - specific historical/technical detail (temperatures,
  dates, mechanisms) that had replaced a terser branch description, verified
  by hand rather than by length alone (18 further cases were judged
  genuinely ambiguous - both sides substantive, differently written - and
  were deliberately left for the branch's own text to win, rather than
  guessed at a second time).
- `req_any` material-substitution groups on 131 nodes (e.g. "cast iron OR
  bronze OR wrought steel, at different quality multipliers") - present only
  in the tree.
- `cat`/`risk` on the 7 nodes (`mat_chile_nitrate`, `mat_cryolite`, `mat_
  gutta_percha`, `mat_natural_rubber`, `mat_newworld_crops`, `mat_platinum_
  bulk`, `mat_quinine`) that a geography-driven realism pass moved from the
  retired `unobtainable` category to `located_material`. Branches still said
  `unobtainable`, which `sim/engine/projects.py` treats as PERMANENTLY
  BLOCKED regardless of civilisation or geography - regenerating without
  this fix would have made seven real, geography-gated materials
  unbuildable in every game, forever.
- `mat`/`lab`/`ph`/`cap`/`up`/`build_yrs`/`yrs`/`conf`/`name` - a systematic,
  one-directional re-costing (median 1.7x-5x higher `ph`/`cap`/`mat`/`lab`)
  that had been applied to the tree directly and never to branches, found by
  the ratio always running the same way across hundreds of nodes rather than
  splitting both ways the way an ordinary two-sided disagreement would.
  `rev` looked like the same shape at first (branch consistently ~5x the
  tree's figure) but turned out to be the opposite case - see below.
- Real `pre` edges on 433 nodes (689 individual edges: 527 ordinary
  prerequisites - e.g. New World crops correctly requiring
  `exp_atlantic_crossing` - plus 162 capability rungs added by hand, unmarked,
  consistent with the realism review's "GATE HARDER" / "MISSING GATE"
  verdicts rather than with `repair`'s (disabled) keyword heuristic).

**What was found and corrected in the OTHER direction - branches carrying a
STALE edge that the tree had already, deliberately, dropped or split.** The
first pass of the `pre` fix above was naive (add whatever the tree has that
the branch doesn't) and it re-broke two already-shipped fixes as a result,
caught only by the regression suite:

- `tl_pneumatic_tyre` and `tl_vulcanized_rubber` regained a direct
  `mat_natural_rubber` prerequisite that a "rubber must be made, not bought"
  fix had deliberately removed in favour of routing through
  `tl_vulcanized_rubber` / `mat_rubber_coagulated`. Removed again, at the
  branch (`45a_transport_land_deep.json`).
- Seventeen nodes (`cn_crane_treadwheel`, `cn_pile_driving`, `en_treadwheel`,
  `pwr_force_pump`, `tr_capstan`, `tr_windlass`, and eleven more) carried a
  stale `cap_power_muscle` prerequisite alongside the tree's correct `cap_
  power_human`, undoing a "human labour and animal labour are distinct
  capability gates" fix. The stale edge was removed at each node's branch
  source, not papered over by editing the tree.

**Two fields held back, not applied, despite branches being real,
deliberately-authored content:** `rev` and (on reflection, in most of its
600+ remaining nodes) `up`. Complaints/30's own "Decision" section from
before this work said outright that this pass had never had its "author
intent" checked, and it was right to be cautious: letting `up` flow
(`branch has a real number, tree has 0`, the majority pattern already
measured above) turns out to zero-then-un-zero exactly the set of
notation/theory/method nodes an earlier fix had deliberately made NOT
ventures (`is_venture()` is `rev > 0 or up > 0`, and the theory nodes were
zeroed on both fields on purpose) - flipping ~1,063 of them back into
openable "shops". `rev` breaks a closer invariant: letting its branch figure
through (median ~5x the tree's) let a fresh household fund `identity_cover`
in one step instead of three, which is a live regression test's whole
point. Both were pushed back to the TREE's value at every branch site that
disagreed (1,063 nodes for `up`, 246 for `rev`) rather than at the mechanism
level, so `merge`'s field-overlay stays a single honest rule and the
special-casing lives in the data, where it is visible, not in the code,
where it would not be. The branch-authored numbers are not lost - they are
still in this file's git history and in every branch file's git blame -
they are simply not yet the ones in play. Doing that review is still the
outstanding work this file already asked for once.

**Three genuine self-cycles, fixed at the source, as expected:**
`mat_bulk_steel` -> `bessemer_openhearth` (a retired duplicate id merged
back into itself), `cap_gas_o2h2` -> `industrial_gases` (same shape), `tl_
electric_starter` -> `electric_starter` (the file's own self-ref-repair
prefixing an unqualified id back onto itself). **Two more, found by actually
running the merge rather than trusting the earlier count:** `lnd_steering_
geometry` <-> `lnd_automobile` and `md2_microbiology_culture` <-> `md2_agar_
media`, both two-node cycles where each side named the other as its own
prerequisite. In both cases the backward edge (steering geometry requiring
a complete automobile; agar media requiring the culturing technique it is
itself a prerequisite for) was the one removed.

**Fixed point, proved:** `merge` -> `repair` -> `apply-caps`, run a second
time immediately after the first, produces a byte-identical `data/tech_
tree.json`. (A bare second `merge`, with no `repair`/`apply-caps` in
between, is NOT byte-identical to itself - exactly as this file's "Decision"
section already said it would look, since `repair` and `apply-caps` add
content `merge` alone does not know about. That is not a fixed-point
failure, it is running one third of the pipeline and comparing it to all of
it.)

**Result:** 2,864 nodes before, 2,864 after. `python3 sim/simulator.py
validate` clean. `python3 sim/test_regressions.py` - 2,147 checks, 0
failures, including `civilisation_prerequisites` (still exactly the same 17
pinned violations), `tierless_schema`, and all five `realism_part0*` topics.
`treetool.py judge`'s mean score is unchanged at 96.0/100, and the grade
distribution moved by single digits (SOCIAL-FLAT defects fell from 135 to
124, because real `traits` are now doing that job instead of a category
guess). The five civilisations' `living_cost()`, `revenue()` and starting
`capital()` are bit-for-bit identical to before this regeneration - holding
`rev`/`up` back is exactly why.
