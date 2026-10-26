# Equivalence baselines at `mr-base`

Hashes of the whole saved state per simulated year, recorded on the base commit of the module migration (`0be2f72`)
with `sim/tests/equiv.py` copied in. Check the current checkout against them:

    python3 -m sim.tests.equiv check docs/architecture/baseline/micro.json --tier micro --base-checkout <base worktree>
    python3 -m sim.tests.equiv check docs/architecture/baseline/full.json --tier full --base-checkout <base worktree>
    python3 -m sim.tests.equiv check docs/architecture/baseline/stress.json --tier stress --base-checkout <base worktree>

`--base-checkout` (a worktree of `0be2f72` with the tool's `equiv*.py` copied into `sim/tests/`) is needed only to
list the differing leaves after a divergence. Moved fields are mapped in `sim/tests/equiv_fields.py`.
