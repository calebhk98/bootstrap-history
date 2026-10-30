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
  `country_literacy_figure`, `country_literacy_ceiling`, `literacy_after_schooling` (quotes), `actor_world` (a fresh world each read), `country_world` (keyed), `concern_counts` (keyed by
  category), `concern_versions`, `actor_staff` and `actor_staff_nationwide` (keyed by trade), `actor_staff_total`, `country_strata`
  (keyed). They replace `legacy_actor_registry`, `legacy_actors_state` and `legacy_agent_world`.
- Commands applied: `AdvanceActors` (no fields), `RecordConquestContact`, `RecordMigrantContact`, `ScaleStrata`, `NoteTraderMargin`.
  `RegisterActor` is not built: no caller sends it. Sent: `RefreshLenderOffers`, `DefaultOnDebt` (finance), `AccrueExperience`
  (production), `ForgetActorOrders`, `NoteActorSale`, `NoteActorPurchase` (markets), `ReleaseStaff` (workforce), applied by
  `sim/engine/bridge_actors.py` until those owners move.
- Reads that the owners have not published yet are bridged in `sim/engine/bridge_actors.py`, one engine call each, under narrow
  names (the catalogue's names for the markets and workforce views are coarser than the calls).
- Added for finance and polity (Phase 6b): views `lender_offers_made` (a copy of the pool's offers), `cash_and_deposit` (keyed), `loans_out`
  (quote), `debt_owed` (keyed), `cast_recorded`, `government_figures` (keyed by country: grant, requisition rate, office rate); commands
  `SetLenderOffers` and `SettleLenderInterest` (`sim/actors/lending.py`). Nothing outside the module writes the purse book any more.

## Width review

Measure: `python3 tools/measure/module_graph.py --modules` (reads, sends and modules depended on; declaration counts, not call counts). This review removed one read-owner edge (the assembly) and two reads; the table below is `READS_BY_OWNER` in `sim/actors/module_spec.py`, which now groups every read under the module that publishes it (the old labels named owners the views once had). Where a view is asked: `grep -n "needs\.<view>" sim/actors`.

### 1. What it depends on, by what it asks

Almost all the width is the world the agents package asks (`ActorWorld`, `sim/actors/world*.py`, the questions of `sim/agents/protocols.py`): an actor decides from prices, people, tax bases, knowledge and credit, and each of those lives in another module. The rest is the seats as parties to the exchange, the actors' own year, and the cast's construction.

| Asked of | What | Where in the module |
|---|---|---|
| scenario | the year, the civilisation's record and opening, game settings, the money and mass-rate words | everywhere (`year`, `civilisation`); `cast.py` builds the opening cast |
| markets | prices of goods and materials, category state and factors, cohort incomes, land rents and idle hours the agent economy computed, the household basket, a country's opening basket and traded volumes | `world_groups.py`, `world_cast.py`, `world_revenue.py`, `world_site.py`, `world_stakes.py`, `world_patronage.py`; sends the notes of an actor's sale and purchase and `ForgetActorOrders` |
| production | what a concern takes, grosses, costs to keep, staffs and ramps (`concern_*`, `industry_*`, `revenue_estimate`, `upkeep`) | `world.py`, `world_enterprises.py`, `world_capacity.py`, `world_seats.py`; sends `AccrueExperience` |
| workforce | staff on the books, the trade supply and the labour market, hours, the trades a place is without | `world.py`, `world_budget.py`, `world_groups.py`, `world_research.py`; sends `ReleaseStaff` |
| polity | a state's funding terms, authority, trait weights, levy shares, patrons and their asks, the founder's standing | `world_budget.py`, `world_patronage.py`, `world.py`; sends `AddScandal` |
| foreign_trade | partners, their books and prices, the landed cost, the home trade, the border duty | `world_trade.py`; one figure in `world_revenue.py`; sends `NoteActorHomeTrade`, `NoteActorTrade`, `NoteCargoLeg` |
| demography, land, agriculture, disease | people, working age, the urban share, land held, farms, the frontier loss | `world_budget.py`, `world_revenue.py`, `world_patronage.py`, `world_capital.py` |
| knowledge, diffusion, mechanics | techniques held, granted and by seat; copy difficulty, disclosure, literacy, research productivity; the mechanics a technology declares | `world.py`, `world_disclosure.py`, `world_budget.py`, `seat_exchange.py`, `literacy_views.py`; sends `ReceiveTechniques` |
| materials, prices | a material's commodity, substitutes and prices | `world_stakes.py`, `world_trade.py`, `world_enterprises.py`, `world_research.py` |
| finance | the market rate, credit room, the state's lending, debt interest and its service share, the founder's credit limit | `world_capital.py`; sends `RefreshLenderOffers` (the year) and `DefaultOnDebt` |
| ledger, coin, freight | the seat's balance and the transfer listening; keeping and theft; route dues | `seat_parties.py` (the seat's purse: `CreditSeat`, `DebitSeat`, `NoteSeatCash`, `RestorePurse`), `world_disclosure.py` (`PayActor`), `year.py`, `world_trade.py` |
| seats, ventures, projects | who plays, their places, patents and dealings; what a seat operates and its business; the project review | `seat_parties.py`, `seat_exchange.py`, `world_disclosure.py`, `world_seats.py`, `world_stakes.py`, `world_review.py` |
| sharing, reporting, content | the shared-answers table the world opens; the log; the declared actor kinds and the trades or materials a scenario lacks | `world.py`, `cast.py`, `world_trade.py` |

### 2. Findings

**(a) Views that mirror one method.** The actors' reads are mostly one view per question the agents ask (the protocol is the question list), so there is little to merge on the reading side. The mirroring is on the owners' side: markets publishes a dozen `agent_*` views that each return one column of the agent economy's tile table (rent at a tile, rent paid by tile, rent per hectare, output by tile, fugitive share by tile, idle hours by trade, cohort incomes and land rents, need floor costs), where the actors ask "what the households earn, pay in rent and leave idle" in four files; that is for the markets review. On the actors' publishing side, the four lending views (`lender_offers_made`, `cash_and_deposit`, `loans_out`, `debt_owed`) each mirror one method of the purse book and have one reader (finance's `capital_market.py`); merging them would only rename the seam, because the real answer is P3 below, after which finance reads its own book. The three `literacy_*` views are three questions of one table (the figure, the ceiling, the preview of a schooling) and have one reader, diffusion: they go with P2.

**(b) Sub-domains reading a separate set of owners.** Section 3, P1 to P5.

**(c) Pass-throughs.** Removed: `registered_seats` (the assembly's) was read only in `find_dealer`, to test whether an id is a seat, while the seats' `seat_list` answers the same ids and is read beside it in the same file. `held_techniques` was declared and asked nowhere. Left: `year.py` sends four commands in a fixed order around the actors' turn (`RefreshLenderOffers`, `AccrueExperience`, `ChargeKeeping`, `ChargeActorsTheft`); they hand no data on, they sequence other modules' year steps from inside the actors' one (P6).

### 3. Done, and proposed

Done, each in its own commit, quick tier green, values unchanged:

- The `held_techniques` read dropped.
- `find_dealer` asks `seat_list()["joined"]` instead of `registered_seats`; the actors no longer depend on the assembly. The fake in `sim/tests/test_seat_dealings.py` no longer supplies `registered_seats`.
- The place coordinates and great-circle distance moved from `world_cast.py` to `sim/geography/places.py` (`distance_between_places`, in the geography interface), because the seats read the whole actors world for one distance (the seats review); `ActorWorld.distance_km` calls it. Test: `sim/tests/test_geography_places.py`.
- The spec's reads regrouped by their real owner.

Proposed, not built. Each is a move of files with the views and commands named; the actors' own edges fall by what the moved files alone read, and the new module takes them on.

- **P1. State finances.** `world_budget.py`, `world_revenue.py`, `world_patronage.py` and the views `army_figures`, `state_budget_figures`, `government_figures`, `harvest_share_taken`, `home_strata_rows`. This file group reads polity (funding terms, authority, levy shares, patrons), demography, land, agriculture, disease, diffusion (research productivity, diffusion index) and part of markets and workforce: most of the width the rest of the module does not share. It still needs the cast (the state is an actor), so the actors would read its figures back for the agents' protocol: the cycle stays, but the actors' own file set reads about half as many owners. Needs a decision on who holds the state actor's record.
- **P2. Reading and teaching, to diffusion.** `literacy_views.py`, `literacy_rules.py`, the literacy part of `country_rules.py`, the commands `TeachLiteracy` and `SchoolLiteracy` and the three `literacy_*` views. Diffusion is the only reader and owns the figure's other inputs; the strata that hold the figure stay in the actors' state and are reached through `country_strata`.
- **P3. Lending, to finance's capital market.** `lending.py`, the four lending views, `SetLenderOffers` and `SettleLenderInterest`. Finance's `capital_market.py` is the only reader of the views and the only sender of the commands (finance review). Needs the purse book (`purses` in `ActorsState`, the agents package) to move to a finance slot; moving state is a decision.
- **P4. Disclosure and patents, beside diffusion.** `world_disclosure.py` (what an invention's makers chose, the live patent, royalties) reads diffusion, seats, knowledge, mechanics and sends `PayActor`. It is diffusion's rule applied to firms; the seats' pure rules it imports (`builders_of`, `disclosure_modes`, `seat_royalties_due`) are already plain functions in the seats' api.
- **P5. The trade view, to foreign_trade.** `world_trade.py` is the only reader of the foreign_trade views and sends three of its commands. A module can already supply a world through the `actor_world_scope` extension point. Needs the trade questions of `sim/agents/protocols.py` split into their own trait.
- **P6. The year's order.** `RefreshLenderOffers`, `AccrueExperience`, `ChargeKeeping` and `ChargeActorsTheft` become phase hooks of finance, production and coin placed after the actors' year. Changes the order only if a hook is misplaced; needs the fingerprint (`python3 -m sim.tests.fingerprint`), so not done here.

The seats as parties (`seat_parties.py`, `seat_exchange.py`, and the commands `ApplyForPatent`, `MakeOffer`, `AnswerOffer`, `GrantLicence`, `SellSeatConcern` the actors apply for the seats) read ledger, ventures, workforce, knowledge and the seats. They are the seats' commands, but a seat-as-party module would need the actors' cast for `find_dealer` while the seats read the actors for the opening cast: one cycle either way, so the party builder stays beside the exchange it feeds.

### 4. Why the remaining edges are needed

Each edge in the table is a question an actor's decision uses (a price, a head count, a held technique, a tax base) or a command it posts (a sale noted, a scandal, a purse credited). They are economic dependencies, not plumbing: an actor that cannot see the market, the people and the state cannot act. After any of P1 to P6 the module still depends on scenario, markets, production, workforce and the people owners, because the agents package is the module's reason to exist.
