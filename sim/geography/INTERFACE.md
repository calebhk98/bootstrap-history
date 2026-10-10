# Geography contract

What the rest of the game may ask about places, and the shape of each answer. Callers import
`sim.geography.api` and use only the calls below; how they are answered (tile grid, layers,
formulas, language) is the geography package's business. Arguments and answers are plain data:
string ids, numbers, lists and dicts. Every call takes an optional `world_map`; without it the
base map answers.

`load_geography(world_map)` (older surface) returns the regions, reach levels, located materials and the
tile grid as one dict, assembled from the map's `tiles`, `regions`, `reach_levels` and `located_materials`
catalogues, so a mod's overlay covers them; a region's tiles are the tiles labelled with it.

Older names on `api.py` (`transport`, `freight_cost`, `settlement`, `tile_names`, the `Geography`
object and its region reach) are outside this contract and are to be replaced by it.

## The map

| Call | Answer |
|---|---|
| `open_map(mods)` | A map handle: the base map with each mod's overlay merged. `mods` is `[(mod_id, mod_root)]` in load order. |
| `tile_ids()` | Every tile id, sorted. Ids are opaque: do not parse them. |
| `tile_facts(tile_id)` | `{id, lat, lon, land_area_km2, coastal, neighbours: [tile_id], climate_class, region}` |
| `tiles_held(civilisation)` | The sorted tiles a civilisation record holds: its `home_tiles` when it lists them, else the tiles its `home_regions` labels name (a region is only a label over tiles). A tile the map lacks is not held. |
| `layer_value(tile_id, layer_id)` | One per-tile value by name (for example `annual_precipitation_mm`, `forest_fraction`), or `null`. |
| `problems()` | `[message]`: everything wrong with the map's data; empty when sound. |

A map is a folder (`data/world/geography/`); a mod's overlay is
`mods/<mod_id>/data/world/geography/` with the same layout. `sim/geography/map_source.py` states
the layout and the merge rules (new ids `<mod_id>:<name>`, `"override": true`, `"remove": true`,
`null` deletes a key).

## Food

`food_potential(tile_id, technique_factors, wild_stock=None)` answers

    {"tile": id, "kcal_per_year": {source_id: kcal}, "total_kcal_per_year": kcal,
     "people_supported": people, "species": {"hunted": [id], "herded": [id], "fished": [id], "foraged": [id]}}

Each source is sustainable yield (crops, pastoral, hunting, foraging, marine and freshwater
fishing; ids come from data). `technique_factors` is `{source_id: multiplier}` chosen by the
caller from what the actor knows; geography does not read the tech tree.

`wild_stock` is the game's `{tile_id: {species_id: share of carrying capacity left}}`, a missing entry
meaning a full stock. `hunted_kcal(tile_id, wild_stock)` gives `{species_id: kcal}` a year's hunting can take
now; `game_food_sources()` names the food source ids hunting goes under; `draw_wild_stock(wild_stock, tile_id, kcal_taken)` returns the stock after hunters take that;
`regrow_wild_stock(wild_stock)` returns it a year later. The game keeps and saves the stock. Labour's
limit on gatherers (sim/labour/food_gathering.py) is applied by the caller, not here.

## Pathways

| Call | Answer |
|---|---|
| `usable_modes([nodes_of_party, ...], cargo="goods")` | `[mode_id]` that carry the class of cargo (`"goods"`, or `"living_stock"`: animals walk overland by the droving mode and ship over water) and that every party can use, from the tech nodes each holds. `modes_carrying(cargo)` lists them whatever they need. |
| `route(origins, destinations, modes, improvements, mode_costs, handling_costs, held_nodes, fastest=False)` | `{legs: [{from, to, mode, km, days, cost_per_tonne}], km, days, cost_per_tonne, inputs: {labour_hours, feed_kg, fuel_kg}}`, or `null` when nothing joins them. The least-cost haul; with `fastest` the fewest-days one (how people travel, not goods). |
| `route_costs(origins, modes, improvements, mode_costs, handling_costs, held_nodes)` | `{tile_id: cost_per_tonne}`: the least cost from any origin to every tile a haul reaches (origins cost 0), priced as `route` prices a haul. One search serves all destinations; the economy's market areas take their carriage costs from it. |
| `reach(origins, modes, days_budget, improvements, held_nodes)` | `{tile_id: days}` within the budget. |
| `dues_hours_per_tonne()` | `{mode_id: hours}` of tolls or port dues per tonne a haul pays when it changes to the mode (the mode's `dues_hours_per_tonne`, with `dues_source` and `dues_conf`). |
| `cargo_loss_per_day()` | `{mode_id: share}` of the cargo a mode loses each day on the road (a herd's strays and wasting; labelled in the mode data). |
| `walking_cargo_modes()` | `[mode_id]` where the cargo is the carrier (droving): no carrier capital, the cargo's feed eaten on the loaded leg only. `droving_carrier(mode_id)` gives `{inputs}`, its physical inputs per tonne-km. |
| `flow_ledger` (module) | Plain-dict ledger `{origin: {destination: tonnes}}` of goods carried in a year: `record_flow`, `pair_imbalance`, `return_fill_share`, `overall_imbalance`. The economy keeps one and prices the carriers' return trips by it. |
| `carriage_rates(mode_ids)` | `{mode_id: {crew_trade, crew_hours_per_tonne_km, handling_hours_per_tonne, edge_classes}}` on level ground for the modes that name a `crew_trade`, from the same physical rates the route search uses. |
| `freight_links(modes)` | `[(tile_a, tile_b, mode, km)]` for edges these modes use with nothing built. |
| `map_of_tiles({tile_id: {lat, lon, coastal, borders}})` | A map of just those tiles with the base map's modes, sea lanes and parameters, for a scenario or test that places its own tiles. |
| `ore_goods()` | `{resource_id: {ore_good: [smelting_recipe_id, ...]}}` for the resources whose catalogue row names ore goods (`ore_goods`), in catalogue order; a mod adds a mineral by adding a row. |
| `works_priced_from_deposits()` | `[resource_id]` whose catalogue row says its mine running cost comes from the deposits' physical works. |
| `mine_demand_goods()` | `{resource_id: [good]}`: the goods whose annual demand a mine of that resource supplies (`mine_demand_goods` on its catalogue row). |
| `parameter_value(parameter_id)` | The value of one map parameter (for example `mining_trade`, the trade whose wage prices mine labour). |
| `build_requirements(tile_a, tile_b, improvement)` | `{km, grade, trade, labour_hours, materials: {material: tonnes}, node, build_years, engineered, crew_people, crew_hours_per_year}` of building a way (`"road"`, `"rail"`, `"canal"`) over the land edge between two bordering tiles, from the terrain (earthwork on the slope, surface and fixed materials from the mode's `construction` data), a `"bridge"` over a land edge between tiles on the same river, or a `"port"` on one coastal tile with no natural harbour (`tile_b` the same tile); or `null` when it cannot be built there. Ground steeper than a way's natural limit is `engineered` at more earthwork, up to its engineered limit. |
| `improvement_key(improvement, tile_a, tile_b)` | The key a built improvement is recorded under: the tile id for a port, the edge key otherwise. |
| `train_carrier(mode_id)` | `{inputs, fuel_material, stock_material, stock_kg}` of a rail mode as a freight carrier (physical inputs per tonne-km, what the fuel and rolling stock are made of), or `null` for a mode that is not a train. |
| `built_km(improvements, improvement)` | Kilometres of a way (`"road"`, `"rail"`, `"canal"`; a bridge's span or a port's quay) the caller's `improvements` record holds, counted as a build is. |
| `worked_deposits(tile_ids, resource_id, year, found)` | The deposits of a resource a party holding these tiles can name, each `{id, name, tile_id, resource, size_tonnes (null: unknown), grade_kg_per_tonne, found_by}`: the catalogue's that were first worked by `year` (or have no date) and the prospected `found` ones. |
| `working_rate_tonnes_per_year(size_tonnes)` | The most a deposit of this size yields a year (`resources_working_share_per_year`). |
| `ore_tonnes_per_tonne(row)` | Tonnes of ore raised per tonne of the resource held, for a `worked_deposits` row. |
| `edge_key(tile_a, tile_b)` | The key a built road or track between two tiles is stored under. |

`improvements` is the caller's record of what has been built, `{edge_key: {"road": true,
"rail": true, "canal": true, "bridge": true, "engineered": true}, tile_id: {"port": true}}`: geography never
stores who built what. A land edge between tiles on the same river is a river crossing: land modes ford it at
their own handling, a mode marked `bridge_only` (rail) cannot cross it without a `bridge`. A built `port`
joins its tile to the sea edges of the bordering tiles that have a harbour. `mode_costs` is money per tonne-km by
mode and `handling_costs` money per tonne per change of mode; without them costs are physical
(labour-hours). `held_nodes` opens sea lanes that need a technique (the monsoon crossing).

## Resources

| Call | Answer |
|---|---|
| `resource_ids()` | Every resource id the map defines (minerals, fuels, gems, salts, plants, animals). |
| `resources_at(tile_id)` | `{resource_id: summary}` of what lies in or grows on a tile. |
| `endowment(tile_id, resource_id)` | `{resource, unit, known, undiscovered_expected, total, expected_undiscovered_count, ceiling}` |
| `known_deposits(resource_id)` | `[{id, name, tile_id, lat, lon, deposit_type, quantity, unit, depth_class, status}]` |
| `deposit_records(resource_id=None)` | the catalogue rows as copied dicts with every field the data carries, for one resource or all, sorted by `order` (rows without one last) then id |
| `mined_before(tile_ids, resource_id, year)` | `{workings: [{id, tile_id, output_per_year, years_worked, years_since_last_output}], unworked: [deposit ids with no working date, not yet worked or no known size], deposits_in_tiles, unit}`; output in the resource's unit, each deposit worked at a fixed share of its endowment a year until worked out |
| `prospect(tile_id, resource_id, effort, seed)` | `[deposit]` found with `effort` person-days: `{id, deposit_type, tile_id, lat, lon, ore_tonnes, contained, unit, depth_class, small_scale}`. The same seed and effort give the same finds, and more effort finds a superset. |
| `supports(tile_id, resource_id)` | 0 to 1: how well a tile suits a living resource. |
| `stand(tile_id, resource_id)` | Area, standing stock and regrowth of a living resource on a tile. |

Hidden deposits are a pure function of the map, the caller's `seed`, the tile and the resource,
so nothing about them is saved; the caller derives `seed` from its own saved state and records
which deposits it has found. Each deposit carries a lat/lon, so a finer map keeps it in place.

## Adding content without code

Every resource row names one mechanism; the mechanisms are code (`sim/geography/mechanisms.py`),
the content is data:

| Mechanism | Read by | For |
|---|---|---|
| `mineral_deposit` | resources | ores, coal, oil: deposit types with density and grade-tonnage models |
| `point_occurrence` | resources | gems: pipes and gravels counted, with a cuttable share |
| `surface_stock` | resources | salt pans, nitre, sulfur, bitumen seeps |
| `biotic_stand` | resources | timber, fibre and dye plants: a climate envelope and stock per hectare |
| `wild_population` | food | game animals |
| `herd_animal` | food | herded animals on pasture |
| `forage_plant` | food | wild plant food |
| `fishery` | food | marine and freshwater fish |

A mod adds `ana_scifi_k3f9:unobtainium` by writing a row with `mechanism: mineral_deposit`, its
deposit types and any known deposits in `mods/ana_scifi_k3f9/data/world/geography/resources/`;
endowment and prospecting then include it. `sim/tests/geography_fixtures/` holds working examples
(a modded mineral, a modded animal, a modded route mode).
