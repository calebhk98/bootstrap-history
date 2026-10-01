# Freight between economies is a two-ox cart over the great-circle distance

**Status:** open

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
