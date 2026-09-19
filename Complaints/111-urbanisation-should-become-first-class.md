# Urbanisation should become a first-class system

**Source:** playtest findings document, LATE-005. **Status:** Major
roadmap-sized feature recommendation, already named in the architecture
plan, and directly interacting with in-flight map work.

## The player's reasoning

Industrial jobs should pull people into towns and cities. Urbanisation
should carry both benefits (thicker labour markets, specialist clustering,
larger consumer markets, knowledge spillovers, infrastructure economies) and
costs (housing shortages, land prices, disease, pollution, fire, food
logistics, water/sewer requirements, unrest). The player notes this would
pair well with "the developing map system."

## How this sits against CLAUDE.md

§3.1 again: a city's population ceiling must not be a fixed historical
number. `docs/architecture/HISTORICAL_SIM_ARCHITECTURE.md` states this
almost verbatim as a worked example: "a city should not have a fixed maximum
population because history says so. Population should be constrained by
food, water, sanitation, mortality, housing, transport, trade access,
political stability, and economic opportunity" - which is close to the
player's own cost/benefit list.

## What already exists, and the map interaction the player's phrase gestures at

`docs/architecture/ENDOGENOUS_COSTS_AND_DOMAINS.md` Part 3's domain table
already names this: Layer 5, "Settlement and urbanisation - cities grow
from jobs, food reach and mortality." `docs/architecture/STATE_OF_THE_
PROJECT.md`'s Milestone 6+ row lists "settlements" among the systems with
no dedicated module yet. So this is an already-planned domain, sequenced
after economy/labour (Layer 3) and infrastructure/trade (Layer 4), for the
same reason as `LATE-003`: a settlement system built before a real labour
market and real freight cost would be inventing numbers for both.

The map interaction is real and worth being precise about, because there
are two separate map systems and a settlement model needs to pick the right
one. `data/world/geography.json` holds both `regions` (21 hand-drawn
records, an 86x size disparity between the smallest, britannia at 230,000
km2, and the largest, americas_north at 19,800,000 km2 - measured directly
via `python3 -c "import json; g=json.load(open('data/world/geography.json'));
areas=[v['land']['land_area_km2'] for k,v in g['regions'].items() if k!='_note'];
print(min(areas), max(areas), max(areas)/min(areas))"`, which returns
`230000 19800000 86.09`) and `land_tiles` (1,139 equal-area tiles, roughly
150,000 km2 each). `docs/architecture/MAP_AND_WEATHER.md` documents which
consumer reads which system as of its own writing, and `sim/world/land.py`
has since moved: it was migrated from the region-keyed extensive margin onto
`land_tiles` in commit `3ecd6a2` ("Land leaves the hand-drawn regions, and
eight numbers in CLAUDE.md get a command", 2026-09-19), confirmed by `grep
-c land_tiles sim/world/land.py` returning multiple hits where `MAP_AND_
WEATHER.md`'s own measurement (written the day before) had found none.
Weather already pools on `land_tiles` too (Stage 0.5 of that document's
staged migration, marked done). Mineral deposits (`sim/world/deposits.py`)
and freight (`sim/engine/economy_freight.py`, region centroids) still read
the 21 hand-drawn `regions` only.

The practical consequence for anyone building urbanisation: it should be
built against `land_tiles`, the finer and now-preferred grain that land rent
itself just moved onto, not against the 21 regions whose 86x size disparity
is exactly the defect `Complaints/46` and `Complaints/50` (closed) already
documented for other consumers. Building cities against the region system
would reintroduce the same defect a third time.

## Size

Roadmap-sized, and its own architecture entry already says it depends on
Layers 3 and 4 being real first (labour market wiring per `Complaints/106`,
freight/trade). Treat this as a multi-month system with a real dependency
chain, not a standalone feature.

## Cross-references

`docs/architecture/MAP_AND_WEATHER.md` for the map split and its staged
migration plan (Stage 4 explicitly discusses growing `land_tiles` further,
which a settlement system would want). `Complaints/46` and `Complaints/50`
(closed) for the region-size defect this should not reintroduce.
`Complaints/106` (ECON-004) for the labour-market prerequisite.
