# Reach and built roads are not read by the engine

**Status:** partly - the engine keeps built roads and track (`state.economy.improvements`) and routes over them (labour reach, relocation, region reach, material freight distance), and the agent economy now prices its hauls over them too; building already takes time (a way opens when its build years, from the crew and the work, have passed), but its labourers are not drawn from the labour market's pools; remaining: bridges, river works, ports and canals, ground steeper than the natural limit, railway carriage rate, market-area partitions fixed at the opening, the reach-band heuristics

Geography routes over tiles by any mode a civilisation holds, with roads and railways as built improvements the caller records (`api.route`, `api.reach`, `api.edge_key`, `api.build_requirements`; `sim/geography/INTERFACE.md`).

## Done

- `state.economy.improvements` ({edge key: {way: true}}) is saved with the game. `Sim.build_way` / `way_quote` (`sim/engine/ways.py`, command `build_way`) price a road or railway from `api.build_requirements`: earthwork on the edge's grade (a bed plus a balanced cut-and-fill bench), surface and fixed materials from the mode's `construction` data (labelled heuristics), labour at the labour market, material at the goods market. Steeper ground costs more; ground beyond the mode's natural limit cannot be built. `sim/tests/test_geography_ways_build.py`, `sim/tests/test_built_ways.py`.
- The agent economy's carriage reads the built ways: `EconomySetup.improvements` (handed in from `state.economy.improvements` at the opening, so the spin-up key covers them), `CarriageTable` passes them to geography's `route_costs`, a `road` carrier is priced in `_carrier_models`, and `Economy.set_improvements` (through `sim/economy/api.py`) rebuilds the carriage table only when the ways change; `AgentEconomy.sync_ways` runs at the start of each economy year. `sim/tests/test_economy_built_ways.py`, `sim/tests/test_port_built_ways.py`.
- Labour reach (`reachable_tiles`) and relocation pass the improvements. Relocation takes the days of `api.route(..., fastest=True)` over the modes held, not a straight-line pace; `RELOCATION_KM_PER_DAY` and the `base_reach` speed-up are gone, and a tile no route joins is refused. `sim/tests/test_relocation_follows_fastest_route.py`.
- `Geography.region_reach` is the fewest days of the fastest route from the tiles held to any tile of the region, over the modes and ways held, banded on a doubling ladder (`reach_band_first_days`, `reach_band_ratio`, both labelled heuristics); a region no route joins is the farthest level. `material_reach` is calibrated against the same table for the civilisation the located-material costs were written for (`located_material_reference_civilisation`), replacing `reach_from_italia`. Reach and mineral access are rebuilt when the techniques held or the ways built change. `civilisation.base_reach` is deleted. `sim/tests/test_reach_from_tiles.py`.
- `material_freight_distance_km` is the km of geography's cheapest route to the nearest producing region (the great-circle distance between the nearest pair of tiles only when no mode joins them).
- The region id "italia" fallback in `economy_mining.py` is gone (a civilisation holding no tile has no woodland ceiling); `sim/tests/test_reach_from_tiles.py` fails if an engine or geography module names a region id.

## What remains

- Railway has no carriage rate in the engine's carrier models (`_carrier_models` in `foreign_routes.py`), so the agent economy cannot haul over a built railway; market-area partitions are fixed at the opening and do not follow later ways.
- A way takes time (build years from the mode's crew), but its labourers are not drawn from the labour market's pools (labelled heuristic in `sim/engine/ways.py`).
- Roads exist only on land edges; bridges, river works, ports and canals, and an `engineered` way over ground steeper than the natural limit, are not built.
- The reach bands are labelled heuristics; deriving the ladder (for example from the carriers' own days per tile) would remove them.

## Folded in

Overlapping issues closed into this one; each closed file keeps its full text.

- 414 (`closed/414-food-potential-is-not-read-by-demography-or-settlement.md`): food potential is not read by demography or settlement (settlement still uses arable times fertility).
- 415 (`closed/415-mining-does-not-read-endowment-or-prospecting.md`): mining does not read endowment or prospecting; a mine should name a found deposit.
- 440 (`closed/440-the-port-does-not-hand-the-economy-site-limits-or-read-its-extraction.md`): the port does not hand the economy site limits or read its extraction.
- 138 (`closed/138-barren-land-has-no-food-but-farming.md`): barren land has no food but farming: the remaining piece is 414 (above).
- 281 (`closed/281-deposit-tile-is-a-coarse-hand-assignment.md`): deposit tile is a coarse hand assignment; surveyed positions per mine (owner: later).
