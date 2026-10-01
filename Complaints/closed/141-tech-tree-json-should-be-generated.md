# The committed tech tree duplicates the branch files

**Status:** closed - pinned by sim/tests/test_generated_tech_tree.py

`data/branches/` is the source of truth for the technology tree
(Complaints/54), and a test now requires `data/tech_tree.json` to equal the
merge of the branches. The committed tree is therefore a build output kept in
git, and every branch edit must be followed by a `treetool merge --write`
commit or the suite fails.

## What it would take

- Build the tree from the branches at load (with the on-disk cache keyed by
  the branch contents, like the price solver cache), and stop committing
  `data/tech_tree.json`.
- Point every reader of `data/tech_tree.json` (engine, tools, tests, docs) at
  the loader.
- Keep `treetool merge --dry-run` as the check that branches merge cleanly.

## Fixed

`sim/engine/tree_source.py` builds the base tree from `data/branches/` and
every reader goes through `load_base_tree()`. A build is kept in memory for the
process and cached on disk under `.cache/tech_tree/`, keyed on a hash of
every file the build reads (branch files, the production catalogue, the trade
registry, and the merge code), so a stale tree cannot be read. Tree-level
metadata (title, goals, goal node) lives in `data/branches/_META.json`.
`data/tech_tree.json` is removed from the repository and ignored.

`treetool.py merge` seeds nothing from an earlier tree; it reports collisions
and data-loss events, and `--out FILE` exports the merged tree. `repair` and
`apply-caps` no longer rewrite the tree (there is nothing to rewrite); `--write`
on them explains that changes belong in the branch files. Fields that had
lived only in the committed file (`kind`, `_internal`, one node) were moved
into the branch files; `kb_level` and `_total_cost` were derived or unread and
are no longer stored.

Measure the cost by deleting `.cache/tech_tree/` and timing
`python3 -c "from sim.engine.tree_source import load_base_tree; load_base_tree()"`
(cold build), then timing it again (warm).
