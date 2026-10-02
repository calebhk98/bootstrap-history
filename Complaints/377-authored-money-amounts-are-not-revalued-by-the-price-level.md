# Authored money amounts are not revalued when the price level moves

**Status:** open

One coin stock now moves every good's price and every wage (Complaint 338): `money_per_labour_hour` carries the price level. The tree's revenue, upkeep and capital figures are priced into the civilisation's coin once, when the tree loads (`sim/engine/money_units.py:price_nodes`), and mining, forest, farm and similar costs are labour-hour constants times that same load-time conversion or `price_index`. A coin stock that doubles doubles goods and wages but leaves those authored amounts where they were, so a concern's takings and a project's quoted cost fall behind a rising price level (and run ahead of a falling one).

Evidence: `sim/tests/test_per_producer_supply.py` checks that goods and wages follow the stock; reading `sim.nodes[node_id]["rev"]` before and after a change of `sim.home_price_level()` shows the same figure.

What it would take: read these amounts through the price level (a read-through on the node's money fields, or re-pricing a per-simulation copy of the tree each year), without re-pricing the shared tree. The capability weight (`economy_production.py:capability_factor`) already works in hours for this reason.

Related: 338, 375, 135.
