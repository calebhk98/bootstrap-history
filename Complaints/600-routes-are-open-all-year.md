# Routes are open all year: no mud season, winter ice or monsoon in the route modes

**Status:** open

Part of Complaint 487 (No diplomacy).

**What is wrong.** A route's cost does not change with the season.

**Evidence.** `data/world/geography/route_modes/`; `sim/geography/freight_cost.py` cites a mud season as a source note only; the route search is date-free.

**Why it matters.** Seasonal closure shapes real freight and the by-employment of the period (see also 530).

**What it would take.** Choose a design: an annualised cost or day multiplier per edge, or a season-aware search; add sourced closure data to the route modes. Record the choice in the complaint.

**Test.** A test compares a route's cost for a mode with and without its sourced closure; `python3 sim/simulator.py validate` passes; no content ids in the engine (4.7).
