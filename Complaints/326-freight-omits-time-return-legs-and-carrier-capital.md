# Freight omits travel time, empty returns and the carriers' capital

**Status:** partly - freight from the carrier is one function (`freight_money_per_tonne_km` in `sim/world/freight_cost.py`) for foreign legs and domestic hauls: travel days from the carrier's pace, the empty return, the carrier's capital at the society's market rate, hulls lost at sea; domestic freight (`economy_freight.py`, through `land_freight_money_per_tonne_km`) now carries the capital and the empty return too (a labelled heuristic: no domestic flow ledger, so the cart returns empty); still open: tolls and port dues, authored river reaches

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

Tolls and port dues per leg, and authored river reaches. The cargo's own
charges are `Complaints/340`; the domestic return leg wants a flow ledger so it
need not assume the cart returns empty.

Related: 135, 323, 338.
