# The committed tech tree duplicates the branch files

**Status:** open

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
