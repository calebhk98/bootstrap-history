# The unit registry has no field rule for mass-per-year quantities

**Status:** open

`data/world/units.json` field rules give a `_display` sibling to plain mass, area and money fields, but none of these mass-per-year fields match a rule, so the text screens print them in tonnes whatever unit the player chose (285): `change_t_per_yr` (the `changes` capacity line, `sim/ui/proto/render_screens_economy.py`), `shortfall_t_per_yr` and `market_available_tonnes_per_year` (market screens). Price-per-mass fields (`buy_per_tonne`, `sell_per_tonne`) are compound units, which 285 leaves for later.

What it would take: a rule for the `_t_per_yr` / `_tonnes_per_year` suffixes with a per-year label, in the data file (outside `sim/ui`). The renderers then read the `_display` siblings like the other routed fields. Command to check: `python3 -m sim.tests --only complaint_285_display_units`.

Related: 285.
