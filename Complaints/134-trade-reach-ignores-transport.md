# How many tradesmen you can reach ignores transport

**Status:** open

The number of people in a trade the founder can reach is a share of the
local town and nation. It should depend on how far people can travel to work
or goods can travel to the workshop: walking or riding reaches a town;
railways, roads with carts, and later cars reach a region or a country.

## Evidence

`sim/engine/labour_capacity.py` and `sim/engine/labour_population.py`
compute reach from town size and population shares; `sim/geography/transport.py`
already models travel cost and speed by technology but reach does not read it.

## What it would take

Derive a reach radius (or travel-time budget) from the transport technologies
held and the land tiles around the base, and count the people in each trade
within it.
