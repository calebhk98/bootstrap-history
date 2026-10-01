# Node revenue was authored against book material costs, and solved costs are lower

**Status:** partly

With `data/prices.json` deleted, every node's material cost comes from the price solver. Authored `rev` figures (book denarii, converted through `money_units`) were written against the old book prices, which for many materials sit well above what the recipes imply. `python3 -c "import sys; sys.path.insert(0,'.'); from sim.engine import data; ..."` over `data.load()` shows the payback (`_total_cost / rev`) of the cheapest node fell: before, no node paid back its whole cost in under about three months; now dozens do, and the fastest two (`el2_three_wire_distribution_system`, `el2_ring_main_distribution`) pay back in about two weeks. `sim/tests/test_early_playtest.py` had to lower `PUMP_PAYBACK_YEARS_FLOOR` to let the check pass.

Why it matters: revenue-to-cost payback drives which projects the player prefers, so a node whose cost fell while its authored revenue stayed is a free-money lever (CLAUDE.md 4.1: revenue should fall out of what the node produces, not an authored number).

Resolution on this branch: `sim/engine/node_revenue.py` sets each node's `rev_hours` at load. A node declaring `annual_output_t` and gating production entries earns that output (split evenly over the materials it makes) at solved prices. Every other node keeps its authored `rev_hours`, held to at most its whole cost over `MINIMUM_PAYBACK_YEARS` (a labelled temporary heuristic). `PUMP_PAYBACK_YEARS_FLOOR` in `test_early_playtest.py` is back at its original value.

What remains: the cap is a heuristic; deriving revenue for every node from what it produces (and replacing the nine declared-output nodes' even split by a real product mix) is the full fix, tied to the node-money-in-physical-units work (`price_nodes` in `sim/engine/money_units.py`). Related: Complaints/123, Complaints/288.
