# The fast suite has six failures on main

**Status:** open

Found while checking the UI branch against main (`bcd8b65`): `python3 -m sim.tests --jobs 2` on main reports six failing checks, none in `sim/ui/`. They hide new regressions, because every run is already red.

- `automation_audit`: the worker crashes at `sim/tests/test_automation_audit.py:29`, `'Sim' object has no attribute 'hire'` (hiring moved to `sim.labour`; the test still wraps the old method).
- `capital_charge`: three checks raise `KeyError: 'lab'` (the test's concern entries lack a field the engine now reads).
- `complaint_45_forest_area_not_region_count`: the worker crashes with `'Sim' object has no attribute 'geo'` (geography moved behind `sim.geography`).
- `complaint_141_year_cost`, "a cached price-table lookup costs well under rebuilding the done set": a wall-clock ratio check that fails when the machine is busy (measured about 0.008 s against 0.014 s); it needs a margin or a count of work instead of time.

Command: `python3 -m sim.tests --only automation_audit,capital_charge,complaint_45_forest_area_not_region_count,complaint_141_year_cost`.

Related: 319, 335 (the capital charge).
