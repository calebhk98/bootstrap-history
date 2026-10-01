# Freight omits travel time, empty returns and the carriers' capital

**Status:** partly - foreign route freight now comes from the carrier: travel days per leg from its pace and the leg's difficulty, the empty return when last year's flows with the partner were one-sided, the carrier's capital (timber for vehicles and hulls, the animals' prices) at the society's market rate, and hulls lost at sea (`sim/world/freight_cost.py`, `sim/engine/foreign_routes.py`); still open: tolls and port dues, authored river reaches, and domestic freight (`economy_freight.py`) which still prices feed and driver only; the cargo's own time, spoilage and loss at sea are 340

Route freight (`sim/engine/foreign_routes.py`) prices feed, crew rations and
hours per tonne-km and a port handling charge per sea leg. It leaves out: goods
tied up on a voyage that lasts months (interest, spoilage), the empty return of
a cart or hull, the price of the carrier itself and its wear, tolls and port
dues, and the sailing seasons. The map has no river legs because rivers lie
inside regions (`data/world/trade_routes.json`), so the river mode is modelled
but unused.

## Evidence

`python3 sim/foreign_trade_report.py` prints each leg's distance and cost per
tonne; none carries a duration.

## What it would take (remaining)

A duration per leg from each mode's speed, an interest and spoilage charge on
the cargo's value, carrier prices from the tree's ship and cart nodes, and
authored river reaches.

Related: 135, 323, 338.
