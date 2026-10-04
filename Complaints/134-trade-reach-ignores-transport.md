# How many tradesmen you can reach ignores transport

**Status:** partly - labour reach counts the towns within a travel-time budget (`reach_population_estimate`); its speed is still a stand-in, and geography's `api.reach` by the modes held (Complaint 416) is not read yet

The number of people in a trade the founder can reach is a share of the
local town and nation. It should depend on how far people can travel to work
or goods can travel to the workshop: walking or riding reaches a town;
railways, roads with carts, and later cars reach a region or a country.

## Evidence

`sim/labour/labour_capacity.py` and `sim/labour/labour_population.py`
compute reach from town size and population shares; `sim/geography/transport.py`
already models travel cost and speed by technology but reach does not read it.

## What it would take

Derive a reach radius (or travel-time budget) from the transport technologies
held and the land tiles around the base, and count the people in each trade
within it.

## Done

`reach_population_estimate` (sim/labour/labour_settlement.py) sums the towns
of every tile within `HIRE_TRAVEL_DAYS` at `travel_speed_km_per_day`; the
trade's people (`_town_people_of_trade`) read it. At walking pace this is the
home town, as before. Remaining: geography now answers `api.reach(origin_tiles, modes, days_budget,
held_nodes=...)` with the modes from `api.usable_modes` (Complaint 416), which should replace the
stand-in speed and the straight-line radius.
