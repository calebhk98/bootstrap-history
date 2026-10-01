# Node revenue was authored against book material costs, and solved costs are lower

**Status:** open

With `data/prices.json` deleted, every node's material cost comes from the price solver. Authored `rev` figures (book denarii, converted through `money_units`) were written against the old book prices, which for many materials sit well above what the recipes imply. `python3 -c "import sys; sys.path.insert(0,'.'); from sim.engine import data; ..."` over `data.load()` shows the payback (`_total_cost / rev`) of the cheapest node fell: before, no node paid back its whole cost in under about three months; now dozens do, and the fastest two (`el2_three_wire_distribution_system`, `el2_ring_main_distribution`) pay back in about two weeks. `sim/tests/test_early_playtest.py` had to lower `PUMP_PAYBACK_YEARS_FLOOR` to let the check pass.

Why it matters: revenue-to-cost payback drives which projects the player prefers, so a node whose cost fell while its authored revenue stayed is a free-money lever (CLAUDE.md 4.1: revenue should fall out of what the node produces, not an authored number).

What it would take: derive each node's revenue from what it produces and the solved price of that output (`NODE_MONEY_FIELDS` in `sim/engine/money_units.py`, the node-money-in-physical-units work), then restore the three-month floor in the test. Related: Complaints/123, Complaints/288 (solved copper and silver look low).
