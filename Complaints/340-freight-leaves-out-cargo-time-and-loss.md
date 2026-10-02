# Freight leaves out the cargo's own time and loss

**Status:** partly - the cargo's interest over the voyage and a wait, spoilage by good (`data/world/spoilage.json`, rates labelled estimates, over the voyage and the wait), its expected loss on sea legs and a merchant margin are a per-good share of the price in the trade clearing (`sim/world/cargo_cost.py`, `sim/engine/foreign_traders.py`); domestic hauls pay the carrier's capital and the cargo's interest and spoilage (`economy_freight.py`); still open: fleet growth from the freight margin over the carrier's cost of capital, and spoilage in the partner quote of `living_stock.py` (it names no material)

Foreign route freight prices the carrier (`Complaints/326`) but not the cargo:
interest on its value while it travels months, spoilage, and the share lost with
a hull. Those depend on the good's value, so they cannot be a per-tonne-km rate
over the route and need a per-good charge in the trade clearing. The opening fleet
and the yards' yearly growth limit are labelled heuristics, and the fleet grows
whether or not carrying pays. Domestic freight (`economy_freight.py`) still omits the
cart's capital.

## What it would take (remaining)

Fleet growth from the freight margin over the carrier's cost of capital; the
material passed to `_trader_cost_share` in `living_stock.partner_quote_per_tonne`.

Related: 323, 326.

Owner decision (2026-10-02): somewhat important, lower priority.
