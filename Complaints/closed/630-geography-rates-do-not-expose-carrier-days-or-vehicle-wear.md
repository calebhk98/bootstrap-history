# Geography's `Rate` does not expose carrier-days, animals per carrier or vehicle wear

**Status:** closed - `Rate` carries `team_days` and `carrier_days` per tonne-km at its pace; a route's legs and `inputs` give team-days, carrier-days and km by mode (`sim/geography/routes_search.py`); `carriage_rates` gives the level `team_days_per_tonne_km` and `carrier_days_per_tonne_km`; the economy's `Haul` and `carriage_wear.Wear` read them, so wear follows the days a haul works on the ground it crosses. Tests: `sim/tests/test_geography_carrier_days.py`, `sim/tests/test_carriage_wear.py`. Founder freight quotes and state supply lines read the same `route` inputs; none of them was changed here.

Part of Complaint 552 (Carriage pays the poor without using their hours or any carriers).

Depends on 629.

**What is wrong.** Carrier needs are not threaded through the crew hours.

**Evidence.** `sim/geography/` (`Rate`), `carriage_crew`.

**Why it matters.** A fleet cannot be sized without them.

**What it would take.** Expose carrier-days, animals per carrier and vehicle wear on `Rate` and thread them through `carriage_crew`.

**Test.** A test: a route's rate reports carrier-days and wear per tonne-km.
