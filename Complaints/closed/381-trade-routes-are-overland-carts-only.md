# Freight between economies is a two-ox cart over the great-circle distance

**Status:** closed - freight is the cheapest route over the map's links by sea, river, caravan or cart; what it still omits is filed as 484

`_route_freight_per_tonne` in `sim/engine/foreign_economies.py` prices the
haul as the land cart already used for domestic freight, scaled by distance and
the regions' `route_difficulty`. There is no sea, river or caravan mode, no
ports, no cargo capacity, no travel time (so no spoilage or interest on goods
in transit), and no choice of the cheapest mode. A route to Han China costs
the same whatever ships or pack animals exist, so only goods worth much per
tonne cross.

## What it would take

Choose the cheapest of the modes `sim/world/transport.py` models (barge,
pack, cart) over a route graph, and add a sea mode. This is also what
`Complaints/138` asks of trade reach.

## Resolved

`sim/world/sea_freight.py` gives a sailing hull's physical inputs per tonne-km;
`sim/world/trade_routes.py` finds the cheapest chain of legs over
`data/world/trade_routes.json`, each leg by the cheapest mode both economies
hold the node for (sea needs ports at both ends, from the geography file's
`coastal` flag); `sim/engine/foreign_routes.py` prices the modes with this
society's feed price and wages. `foreign_route_legs(economy)` returns the legs
for display. Tests: `python3 sim/test_regressions.py --only credible_foreign_trade`.
