# Geography contract

What the rest of the game may ask about places, and the shape of each answer. Callers import
`sim.geography.api` and use only the calls below; how they are answered (tile grid, layers,
formulas, language) is the geography package's business. Arguments and answers are plain data:
string ids, numbers, lists and dicts. Every call takes an optional `world_map`; without it the
base map answers.

Older names on `api.py` (`transport`, `freight_cost`, `settlement`, `tile_names`, the `Geography`
object and its region reach) are outside this contract and are to be replaced by it.

## The map

| Call | Answer |
|---|---|
| `open_map(mods)` | A map handle: the base map with each mod's overlay merged. `mods` is `[(mod_id, mod_root)]` in load order. |
| `tile_ids()` | Every tile id, sorted. Ids are opaque: do not parse them. |
| `tile_facts(tile_id)` | `{id, lat, lon, land_area_km2, coastal, neighbours: [tile_id], climate_class, region}` |
| `layer_value(tile_id, layer_id)` | One per-tile value by name (for example `annual_precipitation_mm`, `forest_fraction`), or `null`. |
| `problems()` | `[message]`: everything wrong with the map's data; empty when sound. |

A map is a folder (`data/world/geography/`); a mod's overlay is
`mods/<mod_id>/data/world/geography/` with the same layout. `sim/geography/map_source.py` states
the layout and the merge rules (new ids `<mod_id>:<name>`, `"override": true`, `"remove": true`,
`null` deletes a key).

## Food

`food_potential(tile_id, technique_factors)` answers

    {"tile": id, "kcal_per_year": {source_id: kcal}, "total_kcal_per_year": kcal,
     "people_supported": people, "species": {"hunted": [id], "herded": [id], "fished": [id], "foraged": [id]}}

Each source is sustainable yield (crops, pastoral, hunting, foraging, marine and freshwater
fishing; ids come from data). `technique_factors` is `{source_id: multiplier}` chosen by the
caller from what the actor knows; geography does not read the tech tree.

## Pathways

| Call | Answer |
|---|---|
| `usable_modes([nodes_of_party, ...])` | `[mode_id]` every party can use, from the tech nodes each holds. |
| `route(origins, destinations, modes, improvements, mode_costs, handling_costs, held_nodes)` | `{legs: [{from, to, mode, km, days, cost_per_tonne}], km, days, cost_per_tonne, inputs: {labour_hours, feed_kg, fuel_kg}}`, or `null` when nothing joins them. |
| `reach(origins, modes, days_budget, improvements, held_nodes)` | `{tile_id: days}` within the budget. |
| `freight_links(modes)` | `[(tile_a, tile_b, mode, km)]` for edges these modes use with nothing built. |
| `edge_key(tile_a, tile_b)` | The key a built road or track between two tiles is stored under. |

`improvements` is the caller's record of what has been built, `{edge_key: {"road": true,
"rail": true}}`: geography never stores who built what. `mode_costs` is money per tonne-km by
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
