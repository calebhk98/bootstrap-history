# Module `actors`

The cast of other actors: governments and firms, their records and registry, and the agents package's world adapters.

**Status:** moved (`sim/actors/`; "As shipped" at the end of this file). Draft for task 1.5 of `MODULE_MIGRATION_TASKS.md`, read-only analysis of `e8b004c` (the head of `sim-module-registry-plan`). No code changed. The tables are generated from the static analysis in `README.md` ("How the numbers were made") and then edited by hand. No committed command reproduces the counts; the scripts were kept outside the repository, so re-measure before acting on one. Names this draft did not open in the source are marked in its hard spots.

## At a glance

| Measure | Value |
|---|---|
| Views / commands proposed | 3 / 2 |
| Old methods and properties owned (after regrouping) | 11 |
| Of those, referenced from another module's mixin code | 5 (0 classed read-only or pure by Appendix B, 5 classed writers) |
| Names used by other modules or by code outside the mixins (ui, agents, ports, mods, function modules) | 29 (5 from mixins, 2 only from outside) |
| Views per used name | 0.10 |
| Views that replace exactly one referenced method and no field (one-to-one) | 1 of 3 |
| Views of other modules it reads | 4, from 3 modules |
| Commands of other modules it sends | 4 |

**Existing surface and files.** Existing: `sim/agents/` (159 files; `api.py` 60 lines, `ActorRegistry`, `Actor`, `Firm`, `Government`, `Household`, `Policy`, `Player`, `register_actor_kind/spawner/world_scope/policy`); engine adapters `sim/engine/agents_port*.py` (22 files). Engine mixin: the registry accessors of `ActorsMixin` (`actors`, `actor_staff_*`, `actor_concerns_in`, `advance_actors`).

## (a) Mixin classes and files absorbed

| Class | File | Methods here | Referenced from other modules |
|---|---|---|---|
| `ActorsMixin` | `sim/engine/society_actors.py` | 11 | 5 |

Methods that stay inside the module (referenced by no other module's mixin code and by nothing outside the mixins): `_advance_actors_year`, `actor_demand`, `actor_staff_nationwide`, `actor_supply`.

## (b) State owned

Paths are today's. Seat-scoped fields live on `state.<section>` as the acting seat's alias (`bind_seat`, `sim/engine/state_seat.py`) and are saved once per seat in `state.seats[seat_id]`; world fields live once on the state. Counts are access sites found by the field scan: a mixin method of another module counts under that module, code in a function module, `sim/ui`, `sim/agents` and the like counts under `<area>`.

Proposed slot: no world state, no per-seat state.

| Today's path | Scope | Read by (outside the owner) | Written by (outside the owner) |
|---|---|---|---|
| none: this module owns derived values only, no stored field | | | |

## (c) Views

Kind is table (one value), keyed (one value per key, computed on first read of the key) or quote (a question with arguments, never cached). Channels are the version channels the owner bumps; `inputs` are other views the value is derived from (a name without a dot is this module's own).

| View | Kind | Seat | Answers | Replaces (old methods) | Replaces (fields) | Inputs | Channels | Callers today |
|---|---|---|---|---|---|---|---|---|
| `cast` | table | no | The registry of governments and firms: records, kinds, the government of a country, firms active, concerns of active firms, staff. Replaces the `actors` handle: 24 members, 94 outside uses (`state` 22, `get` 15, `government_of` 11, `of_kind` 11, ...). | `actors`, `actors.state`, `actors.get`, `actors.government_of`, `actors.of_kind`, `actors.actors`, `actors.home_actors`, `actors.active_firms`, `actors.items`, `actors.values`, `actors.world_for`, `actors.prohibitions`, `actors.concerns_of_active_firms`, `actors.world_of_country`, `actors.ensure_government`, `actors.patent_holders`, `actors.add` | - | - | `cast` | 18 |
| `concern_counts` | keyed | no | How many concerns actors run in a goods category, with a version that moves when the set of concerns changes. | `actor_concerns_in`, `actor_market_version`, `concern_set_version`, `actors.concerns_in`, `actors.version`, `actors.concern_set_version` | - | `cast` | `cast` | 3 |
| `actor_staff` | keyed | no | People of a trade that actors employ at home and nationwide. | `actor_staff_fte`, `actor_staff_nationwide`, `actor_staff_total`, `actor_supply`, `actor_demand`, `actors.home_staff_fte`, `actors.staff_by_trade` | - | `cast` | `cast` | 4 |

**Coverage.** 5 methods are referenced from other modules' mixin code: 4 are replaced by a view here, 1 by a command. 2 more names are used only from outside the mixins (ui, agents, ports, mods). Of all 29 used names, 7 are covered by a view or command through the method itself, 0 through a field alias, 0 are year-phase hooks and 22 are package handle members.

## (d) Commands

| Command | Fields | Replaces | Write sites cited | Refusal causes | Owned fields it writes |
|---|---|---|---|---|---|
| `AdvanceActors` | year | `advance_actors`, `_advance_actors_year`: each actor decides, pays and posts. Methods: `actors.advance`, `advance_actors` | `sim/engine/society_actors.py (advance_actors)`, `sim/engine/step_phase_money.py (money_world)` | none: always applies | - |
| `RegisterActor` | kind, id, record | `register_actor_kind`, `register_spawner`, `register_world_scope`, `register_policy`: mod registries become extension points. | `sim/agents/registry.py`, `sim/agents/policy.py` | `clash` | - |

## (e) Reads and sends

Reads (views of other modules), by provider:

- `coin`: `coin.coin_carriage` (coin_carriage_listening)
- `markets`: `markets.others_trade` (goods_market.others_bought_tonnes, goods_market.others_sold_tonnes); `markets.trade_quote` (goods_market)
- `materials`: `materials.material_pool` (_material_tag)

Sends (commands of other modules):

- `coin`: `ChargeKeeping`, `ChargeTheft`
- `finance`: `RefreshLenderOffers`
- `production`: `AccrueExperience`

## (f) Year phases

Phases of `sim/engine/year_phases.py` `SHIPPED` it takes part in; where a phase is shared with other modules the sub-steps it owns are named (see "The year's shared phases" in the README):

- `money_world`: `advance_actors` (`step_phase_money.py:188`)

## (g) Callers outside the engine mixins that read its views

| Caller group | Uses | Most-used names |
|---|---|---|
| engine/agents_port* | 23 | `actors`, `actor_staff_fte`, `actor_concerns_in` |
| engine/economy_port* | 17 | `actors` |
| engine/(function modules) | 11 | `actors` |
| mods | 3 | `actors`, `actor_staff_total` |
| ui | 2 | `actors` |
| engine/mod* | 2 | `actors` |
| labour | 1 | `actor_staff_fte` |

The scan matches `sim.`, `s.`, `world.` prefixes, so a few counts include unrelated locals; treat them as orders of magnitude.

agents_port*: 23 reads of `actors` and 1 of `actor_staff_fte`; economy_port*: 17; engine functions: 11; mods: 3; sim/labour 1.

## (h) Hard spots and caches

- The `actors` accessor creates `state.actors` on first read, so every static analysis counts every reader of the registry as a writer (this is why 'at least 906' read-only references is a lower bound).
- `SimWorld` (the agents' view of the engine) hands each actor the whole `Sim` member by member; each member it forwards is a declared read after migration (`grep -n 'def ' sim/engine/agents_port*.py | wc -l` counts the forwarding functions).
- Actors act in `act_as`-free world scope but pay through the ledger on behalf of seats.

Caches and version counters held today (feed for task 1.2):

- `_actor_registry` (`society_actors.py`: rebuilt when `state.actors` is replaced)
- `_memo` (`agents_port.py:45`), `sim/agents/registry.py` two version counters, `sim/agents/patent_index.py`, `sim/agents/collection_world.py`

## As shipped

`sim/actors/` holds the module (`module.py`, `cast.py`, `staff.py`, `year.py`, `contact.py`), its rules (`rules.py`), the agents'
world (`world.py`, `world_*.py`, built over the module's reads) and the plain functions the engine's economy still calls
(`flight_values.py`, `land_decree.py`, `delivered_goods.py`). The records stay `ActorsState` (sim/agents/records.py) but live in the
module's world slot; `SimulationState.actors` is a property over it for the callers that read the state directly.

- Views: `cast` (the registry), `cast_state` (the saved records), `state_treasury` (seat), `seeded_actor_registry`,
  `legacy_edge_account` (keyed), `actor_world` (a fresh world each read), `country_world` (keyed), `concern_counts` (keyed by
  category), `concern_versions`, `actor_staff` and `actor_staff_nationwide` (keyed by trade), `actor_staff_total`, `country_strata`
  (keyed). They replace `legacy_actor_registry`, `legacy_actors_state` and `legacy_agent_world`.
- Commands applied: `AdvanceActors` (no fields), `RecordConquestContact`, `RecordMigrantContact`, `ScaleStrata`, `NoteTraderMargin`.
  `RegisterActor` is not built: no caller sends it. Sent: `RefreshLenderOffers`, `DefaultOnDebt` (finance), `AccrueExperience`
  (production), `ForgetActorOrders`, `NoteActorSale`, `NoteActorPurchase` (markets), `ReleaseStaff` (workforce), applied by
  `sim/engine/bridge_actors.py` until those owners move.
- Reads that the owners have not published yet are bridged in `sim/engine/bridge_actors.py`, one engine call each, under narrow
  names (the catalogue's names for the markets and workforce views are coarser than the calls).
