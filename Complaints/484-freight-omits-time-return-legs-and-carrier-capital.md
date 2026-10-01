# Freight omits travel time, empty returns and the carriers' capital

**Status:** open

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

## What it would take

A duration per leg from each mode's speed, an interest and spoilage charge on
the cargo's value, carrier prices from the tree's ship and cart nodes, and
authored river reaches.
