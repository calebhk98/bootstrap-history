# Module `land`

Land and the map: tile ownership, claims, roads and ports, works, colonies, and the geography package.

**Status:** draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

**Moved (ways, works, held techniques):** the ways, the works and the held answer are in `sim/land/` (`ways.py`, `works.py`, `held.py`, rules in `ways_rules.py` and `works_rules.py`), not in a new module: geography's routes, labour, freight and demography already read the ways through land's views, and the catalogue gave them to land. The state is `LandWorld.improvements`, `ways_under_construction`, `works` and `works_under_construction`. Views: `built_ways`, `built_way_km`, `way_quote`, `way_refusal`, `works_at`, `work_capacity`, `work_quote`, `held_techniques`, `partner_gate_refusal`. Commands: `BuildWay`, `FinishWays`, `BuildWork`, `LoseWork`; `BuildWay` and `BuildWork` answer `(ok, text)` as the old verbs did, because the protocol's reply reads a refusal's `cause` only where the old text carried one. `action_results` moved with them (`sim.land.api.action_results`). Reads still bridged: `settlement_tiles` (`bridge_markets.py`), `project_cost_now`, `legacy_constant`.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 7 / 4 |
| Old methods and properties owned (after regrouping) | 37 |
| Of those, referenced from another module's mixin code | 12 (11 classed read-only or pure by Appendix B, 1 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 33 (12 from mixins, 8 only from outside) |
| Views per used name | 0.21 |
| Views that replace exactly one referenced method and no field (one-to-one) | 1 of 7 |
| Views of other modules it reads | 14, from 12 modules |
| Commands of other modules it sends | 2 |

**Existing surface and files.** Existing: `sim/geography/` (76 files, `Geography` behind `GeographyPortMixin`; `api.py` 35 lines, 27 distinct members used from the engine, `queries.py` contract in `sim/geography/INTERFACE.md`). Engine: `TileOwnershipMixin`, `WaysMixin`, `WorksMixin`, `HeldWorksMixin`, `ColoniesMixin`.

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `MiningMixin` | `sim/engine/economy_mining.py` | 1 | 0 |
| `GeographyPortMixin` | `sim/engine/geography_port.py` | 2 | 2 |
| `WaysMixin` | `sim/engine/ways.py` | 8 | 2 |
| `WorksMixin` | `sim/engine/works.py` | 7 | 0 |
| `HeldWorksMixin` | `sim/engine/held_works.py` | 3 | 2 |
| `ColoniesMixin` | `sim/engine/colonies.py` | 7 | 1 |
| `TileOwnershipMixin` | `sim/engine/tile_ownership.py` | 9 | 5 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_owned_tiles_memo`, `_way_crew`, `_where`, `_work_cost_curve`, `build_work`, `built_ways_stamp`, `claimed_tiles`, `finish_works`, `home_land_area_km2`, `lose_work`, `tile_control`, `tile_owner_version`, `way_owners`, `ways_built`, `work_capacity`, `work_quote`, `works_at`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: a world dataclass `LandWorld` and a per-seat dataclass `LandSeat`.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| `state.economy.improvements` | world | campaigns 2, demography 1, production 1, freight 1, <engine-functions> 1 | - |
| `state.economy.tile_claim_conflicts` | world | - | - |
| `state.economy.tile_owners` | world | <engine-functions> 1 | - |
| `state.economy.ways_under_construction` | world | - | - |
| `state.economy.works` | world | - | - |
| `state.economy.works_under_construction` | world | - | - |
| `state.holdings.colonies` | seat | - | - |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `tile_owner` | keyed | no | Who holds a tile (sovereign), and who controls it. | `tile_owner`, `tile_control`, `tile_owner_map`, `tile_owner_version` | `economy.tile_owners`, `economy.tile_claim_conflicts` | - | `tiles` | 4 |
| `tiles_owned_by` | keyed | no | The tiles an actor holds, and the home tiles held. | `tiles_owned_by`, `home_tiles_held`, `claimed_tiles` | - | `tile_owner` | `tiles` | 5 |
| `tile_facts` | keyed | no | Static facts of a tile: climate, soil, resources, distance (the geography package's queries). Replaces the two package handles (`geography` 109 uses, `world_map` 7 uses, 27 members). | `world_map`, `geography`, `geography.api`, `geography.transport`, `geography.climate_temperatures`, `geography.droving`, `geography.borders_among`, `geography.source_tiles`, `geography.route_km_to`, `geography.held_share`, `geography.open`, `geography.material_cost_factor`, `geography.flow_ledger`, `world_map.tiles`, `world_map.catalogue` | - | - | `map` | 25 |
| `transport` | table | no | Built ways and ports, kilometres built, what is held and running, owners of ways. | `built_way_km`, `held_and_running`, `way_owners`, `built_ways_stamp`, `ways_built` | `economy.improvements`, `economy.ways_under_construction` | `tile_owner` | `ways` | 9 |
| `works` | keyed | no | Works at a tile and their capacity. | `works_at`, `work_capacity` | `economy.works`, `economy.works_under_construction` | - | `works` | 0 |
| `colonies` | table | yes | The seat's settlements, candidates and costs. | `colony_rows`, `settlement_spec`, `settlement_candidates`, `settlement_outfit_cost` | `holdings.colonies` | `tile_owner` | `tiles` | 1 |
| `build_quote` | quote | no | Cost and refusal of a way or work of a given kind in a given place. | `way_quote`, `way_refusal`, `work_quote`, `partner_gate_refusal` | - | `tile_facts`, `materials.project_materials` | - | 3 |

**Under the three-caller floor** (task 1.5: a view serves at least 3 callers or is a quote): `works`, `colonies`. Each needs a second consumer found, a merge into a neighbouring view, or a change to a quote.

**Coverage.** 12 methods are referenced from other modules' mixin code: 9 are replaced by a view here, 3 by a command. 8 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 33 used names, 20 are covered by a view or command through the method itself, 0 through a field alias, 0 are year-phase hooks and 13 are package handle members.

**Published as views but still classed as writers** after discounting the lazy creation of `state.actors` (which is what made most of Appendix B's writers; see README). Each is either a read that also fills a cache or lazily creates something, or a real write that must be split into a quote and a command before the view is allowed: `work_quote`.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `TransferTile` | tile, to_actor, cause | `transfer_tile` at conquest, foreclosure or mod gift. Methods: `transfer_tile` | `sim/engine/tile_ownership.py:36`, `sim/engine/campaign_year.py (_take)`, `sim/engine/mod_effects.py` | `tile_unknown`, `same_owner` | `economy.tile_owners`, `economy.tile_claim_conflicts` |
| `BuildWay` | seat, kind, route | `build_way`, `finish_ways`. Methods: `finish_ways`, `build_way` | `sim/engine/ways.py:95-116` | `cut_way`, `not_held`, `cannot_afford` | `economy.improvements`, `economy.ways_under_construction` |
| `BuildWork` | seat, node, tile | `build_work`, `finish_works`, `lose_work`. | `sim/engine/works.py:55-82` | `not_held`, `cannot_afford` | `economy.works`, `economy.works_under_construction` |
| `FoundColony` | seat, tile, spec | `found_colony`, `advance_colonies`. Methods: `advance_colonies`, `found_colony` | `sim/engine/colonies.py:72-100` | `tile_not_free`, `cannot_afford` | `holdings.colonies` |

## (e) Reads and sends

Reads (views of other modules), by provider:

- `disease`: `disease.disease_burden` (_disease_burden); `disease.epidemic_forecast` (regional_disease_loss)
- `finance`: `finance.spending_power` (spending_power)
- `foreign_trade`: `foreign_trade.partners` (partners_in_agent_economy)
- `knowledge`: `knowledge.techniques_held` (projects.done, projects.granted)
- `markets`: `markets.trade_quote` (goods_market, goods_market.purchase_cost)
- `materials`: `materials.project_materials` (input of land.build_quote)
- `mechanics`: `mechanics.mechanic` (mechanic, nodes_with_mechanic)
- `production`: `production.running` (is_venture, running)
- `projects`: `projects.project_cost` (project_cost_now)
- `reporting`: `reporting.event_log` (household.log)
- `stores`: `stores.store` (stores, stores.view)
- `workforce`: `workforce.labour_market` (labour.labour_market, labour.money_per_labour_hour); `workforce.staff` (labour, labour.settlement_tiles)

Sends (commands of other modules):

- `ledger`: `PayEdge`
- `reporting`: `RecordEvent`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `market`: `finish_ways`, which calls `finish_works` (`market_clearing.py:195`, `ways.py:127`)
- `money_world` through `demography`: `advance_colonies`

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| geography | 167 | `geography` |
| ui | 29 | `world_map`, `geography`, `colony_rows`, `settlement_spec`, `settlement_outfit_cost`, `settlement_candidates`, `found_colony`, `way_quote` |
| engine/economy_port* | 20 | `world_map`, `geography`, `held_and_running`, `tile_owner_map`, `tiles_owned_by` |
| engine/(function modules) | 15 | `geography`, `world_map` |
| economy | 11 | `geography` |
| engine/agents_port* | 9 | `geography`, `world_map`, `home_tiles_held`, `held_and_running` |
| constants.py | 5 | `geography` |
| labour | 4 | `geography` |
| agents | 4 | `geography` |
| world | 4 | `geography` |
| mods | 4 | `world_map`, `geography` |
| engine/mod* | 1 | `transfer_tile` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

sim/geography (167 uses of `geography` within itself); sim/ui 29 reads (`world_map`, `geography`, colony and way quotes); economy_port 20; agents_port 9; sim/economy 11; constants.py 5.

## (h) Hard spots and caches

- The `Geography` handle is read by every module (125 references from mixins, `geography.api.*` 76 uses); the view `tile_facts` has to be keyed and cheap, because per-tile reads run in loops.
- Two ownership maps with different meanings (`record.titles` rent rights in the economy; `economy.tile_owners` sovereignty); tile holder and sovereign are different views.
- `tile_owner_map` rebuilds `_owned_tiles` and `_owner_map_seen` lazily by comparing a version (`tile_ownership.py:53-85`).

Caches and version counters held today (feed for task 1.2):

- `__dict__['_owned_tiles']`, `_owner_map_seen`, `_tile_transfers` (`tile_ownership.py:53,67,85`)
- `_held_running_cache` (`held_works.py:19`)
- `__dict__['_geography']`, `_world_map` (`geography_port.py:62,70`)

Detected by the cache scan in this module's mixin files: `engine/geography_port.py:70 __dict__[_geography]`, `engine/geography_port.py:62 __dict__[_world_map]`, `engine/held_works.py:19 __dict__[_held_running_cache]`, `engine/tile_ownership.py:67 __dict__[_owned_tiles]`, `engine/tile_ownership.py:53 __dict__[_owner_map_seen]`, `engine/tile_ownership.py:85 __dict__[_tile_transfers]`.
