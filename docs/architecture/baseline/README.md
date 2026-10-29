# Equivalence baselines at `mr-base`

Hashes of the whole saved state per simulated year, recorded on the base commit of the module migration (`0be2f72`)
with `sim/tests/equiv.py` copied in. Check the current checkout against them:

    python3 -m sim.tests.equiv check docs/architecture/baseline/micro.json --tier micro --base-checkout <base worktree>
    python3 -m sim.tests.equiv check docs/architecture/baseline/full.json --tier full --base-checkout <base worktree>
    python3 -m sim.tests.equiv check docs/architecture/baseline/stress.json --tier stress --base-checkout <base worktree>

`--base-checkout` (a worktree of `0be2f72` with the tool's `equiv*.py` copied into `sim/tests/`) is needed only to
list the differing leaves after a divergence. Moved fields are mapped in `sim/tests/equiv_fields.py`.

## Scenarios re-recorded after a fixed bug

A scenario whose base behaviour was a bug is re-recorded from the build that fixed it; the others stay as the base recorded
them. Each entry names the fix and the commit recorded from:

- `stress.json`, `rome_100ad/seed1/12y/events+stress+2seats`: Complaint 921 (every seat shared the first asker's goal
  closure), recorded at `9c661d02`. Its first year is identical to the base; from the second year the second seat's
  loss-making concern is seized by its creditors. The one-seat scenario recorded at the same commit is identical to the base's.
