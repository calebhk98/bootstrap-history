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
