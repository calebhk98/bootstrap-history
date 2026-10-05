# Freight omits travel time, empty returns and the carriers' capital

**Status:** partly - freight from the carrier is one function (`freight_money_per_tonne_km` in `sim/geography/freight_cost.py`) for foreign legs and domestic hauls: travel days, the empty return, the carrier's capital, hulls lost at sea; foreign legs now also pay tolls and port dues stated per mode in `data/world/geography/route_modes/modes.json` (`dues_hours_per_tonne`, a labelled heuristic; test freight_dues); still open: dues on domestic hauls, authored river reaches, a domestic flow ledger, and droving of live animals (from Complaints/399)

Route freight (`sim/engine/foreign_routes.py`) prices feed, crew rations and
hours per tonne-km and a port handling charge per sea leg. It leaves out: goods
tied up on a voyage that lasts months (interest, spoilage), the empty return of
a cart or hull, the price of the carrier itself and its wear, tolls and port
dues, and the sailing seasons. The map has no river legs because rivers lie
inside regions (`data/world/trade_routes.json`), so the river mode is modelled
but unused.

## Evidence

`python3 sim/foreign_trade_report.py` (script since removed; recover with `git show 97473f1:sim/foreign_trade_report.py`) prints each leg's distance and cost per
tonne; none carries a duration.

## What it would take (remaining)

Dues per leg exist for foreign routes as a labelled heuristic (confidence D, no per-tonne tariff sourced; state customs are the civilisation's import and export duty, not repeated here); a sourced tariff per mode would replace it, and a domestic haul pays none yet. Authored river reaches remain: rivers lie inside regions, so the data has no place for them until the map has river edges. A droving mode (live animals walked to market at the cost of their own feed and loss, not carried at freight rates) is the carriage mode Complaints/399 left open. The cargo's own
charges are `Complaints/340`; the domestic return leg wants a flow ledger so it
need not assume the cart returns empty.

Related: 135, 323, 338.

Owner decision (2026-10-02): can wait a while.
