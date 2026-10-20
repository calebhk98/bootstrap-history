# Routes are open all year: no mud season, winter ice or monsoon in the route modes

**Status:** closed - route modes declare seasonal closures; a haul pays the expected wait

Part of Complaint 487 (No diplomacy).

**What is wrong.** A route's cost does not change with the season.

**Evidence.** `data/world/geography/route_modes/`; `sim/geography/freight_cost.py` cites a mud season as a source note only; the route search is date-free.

**Why it matters.** Seasonal closure shapes real freight and the by-employment of the period (see also 530).

**What it would take.** Choose a design: an annualised cost or day multiplier per edge, or a season-aware search; add sourced closure data to the route modes. Record the choice in the complaint.

**Test.** A test compares a route's cost for a mode with and without its sourced closure; `python3 sim/simulator.py validate` passes; no content ids in the engine (4.7).

## Resolution

Design chosen: an annualised expected wait per edge, not a season-aware search. A route mode may carry `closures` (data/world/geography/route_modes/modes.json): rules with `closed_days_per_year`, `wait_span_km`, a source and a label, and optional conditions on the edge (`edge_classes`, `box` on the edge midpoint, `coldest_month_c_below`, `elevation_m_above`). A haul arrives on a random day, finds the edge shut with chance closed/year and waits half the closure; one wait is paid per passage, so each edge pays its km share of `wait_span_km` (`sim/geography/routes_seasons.py`). The wait is added to the link's days, and the link's money cost is scaled by the extra days over travel days (a waiting day costs what a travel day costs). The result is folded into the compiled link in `routes_compile.py`, so the search code and its cost are unchanged; a leg that waits reports `wait_days`. Shipped rules: Mediterranean winter sea closure (Vegetius), winter coast legs, Baltic/northern sea ice, Indian Ocean monsoon, snow-closed passes for foot, pack, droving, cart and road, river freezing. Tests: `sim/tests/test_route_seasons.py`.
