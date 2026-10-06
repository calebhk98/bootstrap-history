# The labour package imports the engine

**Status:** closed - the reference civilisation comes from `sim/default_civilisation.py` and the technique filter is passed in through `LabourWorld.techniques_available_to`; `KNOWN_VIOLATIONS` is empty. Test: `sim/tests/test_labour_core_walls.py`.

`sim/labour/api.py` declares the wall two-way, but two modules import `sim.engine.solve_prices_core`:
- `sim/labour/wage_provider.py`, lazily, for `DEFAULT_LAND_CIVILIZATION` and `REPO_ROOT`
- `sim/labour/workforce_spinup.py`, at import, for `techniques_available_to`

`sim/tests/test_labour_core_walls.py` pins both as known violations, so a new one fails.

What it would take:
- The engine passes the reference civilisation and the technique filter in. One way is to add them as
  arguments to `wage_provider.reference_civilisation` and `workforce_spinup.spin_up`, called from
  `sim/engine/wage_schedule.py` and `labour_allocation` through `LabourWorld`.
- Then delete the entries from `KNOWN_VIOLATIONS`.
