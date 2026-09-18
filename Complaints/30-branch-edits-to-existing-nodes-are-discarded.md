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
