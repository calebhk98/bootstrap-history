# Freight omits the cargo's time and loss, the carriers' capital and a fleet that grows from the freight margin

**Status:** partly - foreign route freight now comes from the carrier and the trade clearing charges the cargo's own time; domestic freight, tolls and port dues, authored river reaches, spoilage by good and where the fleet comes from are still open

Absorbed: 340 (the cargo's own time and loss) and 323 (foreign trade has no balance of payments and no fleet; the balance of payments is built, the fleet heuristics are carried here).

## Built

- Route freight (`sim/world/freight_cost.py`, `sim/engine/foreign_routes.py`) comes from the carrier: travel days per leg from its pace and the leg's difficulty (kept on every leg), the empty return when last year's flows with the partner were one-sided, the carrier's capital (timber for vehicles and hulls, the animals' prices) at the society's market rate, and hulls lost at sea.
- The cargo's interest over the voyage plus a wait, its expected loss on sea legs and a merchant margin are a per-good share of the price in the trade clearing (`sim/engine/foreign_traders.py`).
- Goods are paid in coin that moves between a per-partner ledger and a coin stock (`sim/world/balance_of_payments.py`, `sim/engine/foreign_payments.py`): a persistent deficit drains the stock, never below zero, and lowers the traded-price level so imports get dearer and exports cheaper (the price level touches only traded prices: 135). Each route has a fleet whose yearly lift caps the tonnes that cross and which grows from what it could not carry within what yards can build.
- Evidence: `python3 sim/foreign_trade_report.py` prints each leg's distance and cost per tonne.

## Still open

- Domestic freight (`sim/engine/economy_freight.py`) prices feed and driver only: no cart or hull capital, no capital charge.
- Tolls and port dues, sailing seasons, and authored river reaches (the map has no river legs because rivers lie inside regions in `data/world/trade_routes.json`, so the river mode is modelled but unused).
- Spoilage by good (interest, wait and sea loss are charged; spoilage is not).
- The opening fleet and the yards' yearly growth limit are labelled heuristics, and the fleet grows whether or not carrying pays: fleet growth should follow the freight margin over the carrier's cost of capital. Hulls, pack strings and carts as capital with a build cost, so a route's tonnage is what its carriers can lift (`sim/world/sea_freight.py` gives the physical inputs per hull). This is also why `enabled` for foreign economies is on only because flows are small (346).

Related: 346, 135, 109.
