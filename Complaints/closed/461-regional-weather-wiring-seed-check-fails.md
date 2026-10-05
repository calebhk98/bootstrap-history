# regional_weather_wiring fails its old-seed check

**Status:** closed - the seed gained the game's weather salt on purpose (complaint 384), so the old expected value was stale; `test_omitting_region_mixes_in_no_region_ingredient` in `sim/tests/test_regional_weather_wiring.py` pins what still matters: no region component without a region

`test omitting region reproduces the old civ year only seed` fails: `AssertionError: 4249780299 != 134060541`. It fails the same way on `main` at the merge of pull request 27 (`da86abf`), before the package split, so it is not caused by that work.

Evidence: `python3 -m sim.tests --only regional_weather_wiring` (one failure of the topic's checks).

What it would take: find whether the seed derivation for a weather draw without a region changed on purpose (then the test's expected value is stale) or by accident (then the derivation is the bug).

2026-10-05: re-measured on `a277b59` (the merge of pull request 35): `python3 -m sim.tests --only regional_weather_wiring` still fails this one check with the same numbers, so it is not stale and stays open.
