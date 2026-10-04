# Geography api has no travel speed for the transport an actor holds

**Status:** open

Labour's trade reach (complaint 134) counts the towns within a travel-time
budget of the base. `sim/labour/labour_settlement.py` `travel_speed_km_per_day`
is the stand-in: walking pace times the civilisation's `base_reach`. It does
not read the technologies held, because `sim.geography.api` exposes no
function from held technologies to a travel speed (`transport.py` models
animals and freight cost per tonne-km, not people's speed by tool).

Wanted from the geography owner, in `sim/geography/api.py`:

    travel_speed_km_per_day(technologies_held, from_tile, to_tile) -> float

the best overland or water speed an actor holding those technologies gets
between two tiles (roads, carts, rail, ships, engines), derived from the
transport models, not a table. With it, replace the body of
`travel_speed_km_per_day` in labour_settlement.py; reach_population_estimate
already takes a speed. Better still, `tiles_within_travel_days(technologies_held,
from_tile, days) -> list of tile ids`, so reach follows routes and not
great-circle distance.
