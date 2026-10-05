# The test suite fails on main

**Status:** closed - fast checks repaired: `automation_audit` patches the labour object's `hire`, `capital_charge` builds a node with the current fields and patches `sim.labour.api.production_data`, the price-table check in `complaint_141_year_cost` counts table rebuilds instead of seconds, and `complaint_45_forest_area_not_region_count` already passes. Of the slow items, "gaining a deputy is announced" passes and the weather seed check is Complaint 395 (regional weather); `round2_policy_hazards_options` was not re-run in this pass.

On main at the merge of pull request 30, `python3 -m sim.tests --only automation_audit,capital_charge` fails before any geography change:

- `automation_audit`: the module patches `Sim.hire`, which no longer exists (`AttributeError: 'Sim' object has no attribute 'hire'`), so the whole topic crashes at import.
- `capital_charge`: three checks raise `KeyError: 'lab'`.

With `--slow`, main (pull request 31) also fails `regional_weather_wiring` (the seed check of Complaint 395), `round2_policy_hazards_options` (payroll trimming, hiring on a rich economy, England's full state size: the other 395) and the slow check "gaining a deputy is announced" in `household_capacity_and_literacy`.

A further check, "a cached price-table lookup costs well under rebuilding the done set", is a wall-clock comparison that failed once under load in a full run and passes alone; a timing ratio is not a stable assertion.

What it would take: point the automation audit at wherever hiring lives now (`sim/labour/`), find what the `lab` key became for the capital charge, and make the price-table timing check measure work rather than seconds.

Also seen on main at pull request 31 (from the UI branch's full run): `complaint_45_forest_area_not_region_count` crashes with `'Sim' object has no attribute 'geo'` (geography moved behind `sim.geography`).
