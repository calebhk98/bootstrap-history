# Module migration tasks

**Status:** in progress on branch `sim-module-registry-plan`, base `mr-base` = `0be2f72` (a local tag; the code there is identical to the branch head before phase 0). The design is
`MODULE_REGISTRY_PLAN.md`; this file is the execution order and is ticked as each task merges. The work lands as one
pull request when every box is ticked. `main` is frozen for the duration (owner decision 2026-10-25).

## Resume here (paused 2026-10-27 for the usage limit)

The integration branch is verified through `aed6e564`: the full equivalence tier is identical at `0c5c18aa`; stress,
protocol goldens and `--slow` are identical or green at every later merge. Two branches are pushed but **unverified and
not merged**:

- `mr/forwarders-out` (`0909206c`): engine, bridge, mod and test callers moved off `Sim`'s forwarders, forward file by
  forward file (mechanics, polity, prices, production, projects, ventures, reporting, resources, seats in progress).
  Next: run the quick tier, the protocol goldens and micro on it, fix what they find, merge; then the remaining
  forward files and `core_properties.py`.
- `mr/kernels` (`b635212b`): Complaint 661, `sim/assembly/kernels.py`, the least-cost route tree and fetch-wage kernels
  with stored samples, `api.kernel`, four tests. Next: the quick tier, `--slow --only mod_kernels_smoke`, micro, then
  merge.

Then, in order: rewrite the shipped code mods onto the mod interface and Complaint 840 (phase 7); the purses and the
projects record's shared sets (phase 3); phase 9 (`--slow`, long tier and fingerprint against `mr-base`, regenerate the
shipped openings, fix the bugs kept on purpose: Complaints 681, 760 to 765, 790, 800, 810, 840; docs; the real PR).

Operating rules: only the orchestrating session merges; agents work in worktrees on `mr/<task>` branched from the
integration branch, own named files, never edit `core.py`, `state.py`, `state_seat.py`, `core_seats.py`,
`year_phases.py` or `saveload.py` (they describe the wiring instead), run only targeted topics and the micro
equivalence tier, and hand long runs back. After every merge the orchestrator runs the equivalence tool and the quick
tier, and reverts on red.

## Modules moved

Each row merged with the micro equivalence tier identical to the base and the protocol transcripts unchanged.

| Module | Package | Notes |
|---|---|---|
| ledger | `sim/ledger/` | owns the tonnes ledger and the pool of capacity keys swept out of it; every money path outside the agents' and the economy's own books is a ledger command; still to do: the purses (`HouseholdState.capital` and the actors' `Purses`), reached through `legacy_acting_household` and `legacy_household_actor`; Complaint 790 |
| living stock, defence stores | `sim/living_stock/`, `sim/defence_stores/` | |
| projects | `sim/projects/` | starting, progress, completion, staffing, exclusions, running gates, closures, reviews; its seat state holds the exclusions and staffing records; still to do: `active`, `bountied`, `failed_attempts`, `paid_towards`, `operating` and the businesses (written by finance, hazards, production and the household facade), `cause_book.py` |
| ventures | `sim/ventures/` | what a concern ties up and earns, opening by hand, the founder's sale, coverage roll-out; still to do: the businesses, plants and `mothballed` on the projects record (written by production, finance, hazards and the household facade) |
| coin | `sim/coin/` | carriage is the ledger's `transfer_surcharge` point |
| campaigns | `sim/campaigns/` | |
| reporting | `sim/reporting/` | the seat log and audit trail; world events are hazards' |
| mechanics | `sim/mechanics/` | a query service: many narrow views, no state |
| freight | `sim/freight/` | |
| agriculture | `sim/agriculture/` | the farm holding is demography's |
| foreign trade | `sim/foreign_trade/` | trader cargo legs stay in the agent economy's record until markets moves |
| diffusion | `sim/diffusion/` | literacy, adoption, disclosure |
| knowledge | `sim/knowledge/` | the seat state holds what a seat holds, was granted, finished when, has heard of and has forgotten, written only by its commands and published as frozensets (`techniques_held`, `techniques_granted`, `techniques_revealed`, `techniques_by_seat`) and a copied dict (`done_year`); the tree's closure, critical path and hard prerequisites and the losable nodes are its views; still to do: the tree itself and the fog switch (`legacy_tree`, `legacy_fog`); Complaint 735 |
| resources | `sim/resources/` | mines, deposits, forest, nitre beds; Complaint 730 |
| hazards | `sim/hazards/` | dated shocks, world hazards, relief, the world event log, the output factor; Complaints 740, 741 |
| materials | `sim/materials/` | supply, demand, the throttle (a pure quote plus `ApplyThrottle`), electricity, project materials |
| seats | `sim/seats/` | joining, ending, handover, sight, dealings, goals and win conditions, founder death (`EndRun`); the registry and `act_as` stay on `Sim` |
| prices | `sim/prices/` | the price solver's callers read quotes; the spin-up cache follows modules named in `DISCOVERS` |
| polity | `sim/polity/` | standing, state notice, demands, patronage, the society's value weights; Complaint 760 |
| disease | `sim/disease/` | the epidemic year runs inside demography's regional step, as two commands around the externality door |
| demography | `sim/demography/` | the three age bands, regions, urban share, food eaten, the farm holding; the age bands are the only copy (no `Sim.population` mirror) |
| actors | `sim/actors/` | the cast, its records and the actors' world (was the engine's `agents_port*`); `state.actors` is a property over the slot |
| workforce | `sim/workforce/` | the labour package behind `WorkforceWorld`; the staff, hours and pay books are its seat state; still to do: its remaining `legacy_state` reads (purse, bondage, built ways, the projects' sets) and cached views once Labour's in-place writes become commands; Complaints 762, 764 |
| land | `sim/land/` | the owner map, colonies, the map and geography handles, the built ways, the works and improvements, the held techniques; `BuildWay` and `BuildWork` answer `(ok, text)` so the protocol replies keep their wording |
| markets | `sim/markets/` | the market book, flows, clearing, goods categories, household demand ratios, the goods market object and the port over the agent economy (`port*.py`, `goods_*.py`; the module builds `economy` and `goods_market`, which read the game through `PortWorld`); `Sim.economy` and `Sim.goods_market` are forwarders. The household need model is the module's (`household_needs.py`, `household_views.py`: `household_demand_units`, `household_basket`, `home_household_tonnes`, `partner_household_demand`; it reads the bridged `installed_mod_ids` and `household_need_data`, which need the mods directory and the engine's mod loader, so they stay bridged; the substitute views `materials_serving`, `material_substitutes`, `material_serves_a_need` (`need_substitutes.py`), the credit views `agent_rate`, `agent_credit_room`, `agent_economy_opened` and the `FoundBankFromOutside` command are the module's). Still bridged: the repricing of the opening's money (`RepriceOpeningMoney`). The shipped openings must be regenerated (`simulator.py openings`): the spin-up source moved, so the shipped keys no longer match |
| finance | `sim/finance/` | credit limit, interest and arrears, insolvency, debt bondage, purchases and affordability, the seat bank; the agent economy's own credit and bank files in `sim/economy/` stay behind its api; Complaint 763 |
| stores | `sim/stores/` | the declared mod stores and their saved values (`StoresWorld.values`); a game's declarations are the answers to its `store_declarations` point (the base game's and the mods' data through the bridge views `base_store_declarations` and `data_store_declarations`, and mod code through `api.store`); `Sim.stores` is a property over the module's `store_book` view |
| production | `sim/production/` | revenue, upkeep, concerns and their book sales, volume, industry depth and learning, techniques in use, capability; still to do: `projects.operating` and the revenue caches on the household, `node_rederive.py` (shared tree pricing), and its `legacy_game` reads |

The slow suite (`python3 -m sim.tests --slow`) is green at `b0b3a8d0`. Full equivalence tier identical at the prices, demography, land, markets, production, projects last-mixins (`161acde1`, which includes the ledger money) and phase 6 (`0c5c18aa`, which includes the year composition) merges; stress tier and protocol transcripts identical after each module (re-run with `python3 -m sim.tests.equiv check docs/architecture/baseline/<tier>.json --tier <tier>`).

Phase 6 (a) is done: `sim/ui/` reads views and sends commands (`tools/check_ui_views.py` checks every name it uses exists; a 168-command protocol session gave identical replies to the base). Still to do in phase 6: about 490 forwarders in `sim/engine/forward_*.py` and `core_properties.py` that engine code, mods and tests still call, and the mixin fakes in the tests (137 files, mostly the labour package's own mixins). Next: those forwarders' engine callers, the projects record's shared sets and the purses; phase 7 in progress (the mod registries other than the ui's are extension points of their owners: `mod_code.py`, `docs/architecture/MODULE_REGISTRY_PLAN.md` section 4.5); then 8 and 9.

## Task list

### Phase 0: tools and baseline (blocks everything)

- [x] **0.1 (orchestrator)** (base `0be2f72`, worktree `../base-wt`; quick tier 13123 checks green) Tag `mr-base` at the branch head. Make a pinned base worktree at `mr-base` and never edit it. Record the quick-tier counts.
- [x] **0.2** (`sim/tests/equiv.py`; the slow build was the cold agent-economy spin-up, the tool uses the short spin-up and the disk cache) Profile why a fingerprint scenario build takes over 200 s, when the quick tier builds every civilisation in seconds (`harness._warm_starts`). Fix the slowness if it is in test tooling. Then build `sim/tests/equiv.py`:
  - It hashes each field every year and reports the first diverging year, field and key, plus the random state, so a draw made in a different order can be told apart from a changed value.
  - It has a micro tier (about 2 scenarios × 15 years, aiming under a minute) and a full tier (4 scenarios × 40 years).
  - A field-path resolver table, `sim/tests/equiv_fields.py`, maps each baseline field to candidate paths. A move appends its new path in the same commit. This is test tooling, not a save migration.
  - Acceptance: base checked against base is clean, and a planted extra random draw is caught and named.
- [x] **0.3** (`sim/tests/test_protocol_golden.py`, 83 of 99 commands; Complaint 680 found) Record protocol golden transcripts at `mr-base`: scripted command sequences on a fixed seed, saving the JSON replies. Behaviour tests compare reply values, not wording (CLAUDE.md section 6). This closes the protocol gap before anything moves.
- [x] **0.4** Put the measurement scripts from the appendix in `tools/measure/`. Acceptance: they reproduce 1559 and 906 at `mr-base`.
- [x] **0.5** Write `tools/done_check.sh`, which prints the done-criteria counts below. Record the equivalence baseline (micro, full and long) at `mr-base` and commit the hash file.

### Phase 1: framework (`sim/modules/`, engine unchanged)

- [x] **1.1** The core types (`sim/assembly/`, tests `test_assembly_*.py`):
  - `ModuleSpec`, `ViewSpec`, derived and keyed views, quotes, the command base class (refusals use `sim/refusal.py`);
  - assembly and its errors: a missing provider, a doubled provider, removal refused naming the reader, an optional view absent;
  - phases tied to `year_phases`;
  - extension points with one clash rule, view adjusters, extend layers;
  - the assembly record and the dependency printout.
  - Tests are on toy modules, one function per test.
- [x] **1.2** View freshness (`sim/assembly/clock.py`, `views.py`):
  - Each owner keeps a version per view, plus a version per seat for seat-scoped views.
  - A derived-view cache stores the tuple of its input versions and recomputes when the tuple changes.
  - Owner commands bump the versions of the views they touch.
  - In debug mode (on by default), a shadow check recomputes every N reads and raises, naming the view, if the cached value differs. This catches a missed bump.
  - Seat switch becomes one `bump_seat(seat)`.
  - Load calls `assembly.rebind(state)`, which drops caches and rebinds the module instances.
- [ ] **1.3** State registration (slots, save record and seat rebinding done: `sim/assembly/slots.py`, `sim/engine/game_assembly.py`; deriving `ALL_STATE_CLASSES`/`SAVE_FIELDS` waits for the first moved fields):
  - `ModuleSpec.owns` registers dataclasses into a per-module slot on `SimulationState` and `SeatState`, saved through the existing dataclass walk.
  - `ALL_STATE_CLASSES` and `SAVE_FIELDS` are derived from the assembly.
  - Seat aliases are declared per module, and `bind_seat` loops over them.
  - Removing a module removes its fields.
  - The orchestrator applies the hub-file wiring.
  - Acceptance: a toy module's state survives a save round trip, and it appears and disappears in the save fields as the module is added and removed.
- [x] **1.4** (`sim/tests/module_harness.py`; the rules are in `MODULE_MIGRATION_GUIDE.md`) `sim/tests/helpers/views.py`: `make_views(**plain_dicts)` and a recording `FakeCommands`. Also the test migration rules in `docs/architecture/TEST_MIGRATION.md`.
- [x] **1.5** (`catalogue/`) Catalogue drafts in `docs/architecture/catalogue/<owner>.md`, one per Complaint 508 owner:
  - Group cross-mixin reads by what the consumer wants to know.
  - Map writes onto the command vocabulary.
  - Draft limits: a view serves at least 3 callers or is a quote; about 25 views at most per owner.
  - Also inventory every cache, port object and invalidation point. This feeds 1.2.
- [x] **1.6** Merge phase 1. The equivalence tool must be unchanged and the quick tier green.

### Phase 2: prototype gate (serial)

- [x] **2.1** (`sim/living_stock/`, `sim/defence_stores/`) Living stock (`living_stock*.py`, `defence_stores.py`, `food_relief.py`) becomes a module:
  - Its rules become plain functions over views.
  - It writes through goods, pay and settle commands.
  - Its tests are rewritten.
  - During the move, the old mixin methods become one-line forwarders, deleted when the mixin goes.
- [x] **2.2** (`sim/ledger/`) The ledger as a command owner. First, `Transfer`, `Pay` and `PayEdge` commands wrap today's `ledger.transfer` and `pay_edge`. Then a few call-site batches are routed through them. Every other path that moves money is listed for phase 3.
- [x] **2.3** (`sim/projects/`) Project starting (`projects_starting.py` `StartingMixin`, `step_phase_project_start.py`, staffing, ventures). It is the heavy reader: credit, production, labour, capabilities, fog and mechanics.
- [x] **2.4** (`PROTOTYPE_REPORT.md`: go; the read limit is dropped) Gate report, `docs/architecture/PROTOTYPE_REPORT.md`. Stop and regroup if any of these holds:
  - a domain's catalogue comes out near one view per old method (more than 20% one-to-one);
  - a domain needs more than about 15 declared reads;
  - there is an equivalence divergence nobody can explain;
  - the quick tier slows by more than 15%, or the micro tier by more than 25%.

  Otherwise, revise the framework and catalogue, and record what changed in `MODULE_REGISTRY_PLAN.md`.

### Phase 3: owners of conserved quantities

- [ ] **3.1** Ledger, in batches of about 15 files by directory:
  - Route every `ledger.transfer` site, every `pay_edge` site and the other paths that move money.
  - Remove the direct `.capital =` and `.money =` writes and the `record.book.transfer` calls outside the ledger module.
  - Goods move through `MoveGoods`.
- [ ] **3.2 to 3.4** Workforce hours (`CommitHours`), land (`TransferTile`), people (`KillPeople`, `MovePeople`). Two of these may run at once only if their file sets are disjoint. Proof: the full equivalence tier, the conservation tests and a save round trip.

### Phase 4: walled packages become modules (serial)

- [ ] Labour becomes workforce, geography becomes land, the economy becomes markets, and disease becomes its own module.
- [ ] Their adapters (`LabourWorld`, `GeographyWorld`, `SimWorld`) become declared view lists, and the lazy port properties go.
- [ ] After the phase: the long equivalence tier.

### Phase 5: remaining mixins, leaves to hub

- [ ] **5.0 (read-only agent)** Re-measure and fix the order. Expected: campaigns, revolts and captives; hazards; coin and theft; foreign trade; society; projects; production; the older economy code last.
- [ ] **5.x** One topic per task. Up to 2 agents at once on topics that neither read each other nor share files.
  - A task is done only when its mixin leaves `Sim`'s bases, its forwarders and its test fakes are gone, and its caches are views.
  - The orchestrator runs the full equivalence tier and the quick tier per merge, and the long tier every fifth merge.

### Phase 6: UI and protocol

- [ ] `ui_port` and the forwarders in `core_properties.py` become view lists and commands.
- [ ] The protocol golden transcripts from 0.3 must still match.
- [ ] A final sweep of leftover mixin fakes in the tests.

### Phase 6b: ownership boundaries (added after the review on PR #108)

The migration is done when ownership boundaries hold, not when `Sim` is thin. `tools/measure/coupling.py` counts only the
classes left in `Sim.__mro__`, so it measures the inheritance left on `Sim`, not the coupling between modules; that is
`tools/measure/module_graph.py` (both printed by `tools/done_check.sh`). Measured at `58d70078`: 30 modules, 303
dependency pairs between modules plus 29 modules depending on the engine bridge, a strongly connected group of 27,
254 reads answered by the bridge, 80 reads of `legacy_*` views; the widest are markets (24 modules depended on),
actors (21), hazards, workforce (20 each), projects (19).

- [ ] Guarded reads: a reader cannot change another module's view answer (`sim/assembly/read_guard.py`, on with
  `BH_GUARD_VIEW_READS=1` in debug games). Inventory every write it refuses on the slow tier and the equivalence runs,
  turn each into the owner's command, then switch the guard on by default in debug games. The guarded slow tier at
  `2294c07f` refused no write (its only failures were Complaint 866 and the goldens' time limit); the guarded micro tier
  is next.
- [x] No `legacy_game` or `legacy_state` reads: production, workforce, finance, polity, demography and agriculture read
  named views and send owners' commands; the bridge views are deleted. The one whole-game handout left is `provider_game`,
  the mod contract (phase 7). Measured after: 45 reads of `legacy_*` views (80 before), 241 reads answered by the bridge
  (254 before).
- [ ] No other `legacy_*` view that hands out a live object (`legacy_projects`, `legacy_world_map`, `legacy_seats`,
`legacy_economy`, `legacy_labour` and the rest: `python3 tools/measure/module_graph.py`).
- [x] The `scenario` module (`sim/scenario/`) owns the game's setup and clock: the civilisation, the configuration, the modes
  (events, manual, fog, fuzzy estimates), the year (only `AdvanceYear` moves it), the horizon, the danger and project limits,
  and the text helpers that follow the coin and the player's units (`money_text`, `mass_text`, `plain_number`, ...). Its
  inputs (another civilisation's file, a kit's worth, the unit registry) arrive in `OpenScenario`, so it reads no view. Left
  on the engine: the unit options (`sim/engine/units.py`, process-global UI state) that `Sim` hands over as a callable.
- [x] Actors publish `has_state`, `countries`, `organised_factions`, `home_country`, `state_knowledge`, `holder_treasury`, `partner_catch_chance`, `harvest_share_taken` and `legacy_country_literacy` (`sim/actors/country_views.py`, rules in `country_rules.py`). Actors also build the opening cast from the scenario's `opening_civilisation` and the partners' `civilisation_record`. `declared_actor_kinds` is published by `content` (below).
- [x] The mod loader is the `content` package (`sim/content/`, door `api.py`) and the `content` module owns the game's mods directory (`OpenContent`, sent by `game_assembly.build`). It publishes `mods_directory`, `installed_mod_ids`, `map_overlays`, `household_need_data`, `declared_actor_kinds` and `data_store_declarations`, computed from that directory by `sim/content/views.py`. Still bridged: `data_command_specs` and `data_figure_specs`, because validating a declared state path needs `Sim` and the `@readable` mark (`ui_data.check_state_path`).
- [x] The static tables moved out of `sim/engine/data.py` into `sim/content/`: the production catalogue, trade registry and tree
  builder (`catalog.py`, `tree_source.py`, `tree_merge.py`), `trades.py`, `tech_effects.py` and `foreign_economies.py`. The `content`
  module publishes `trade_records`, `trade_notes`, `trades_absent`, `trade_family`, `tech_effects`, `foreign_economy_records` and
  `not_traded_materials`, read once per game from its directory. The engine keeps import-time copies of the tables for its own readers
  (Complaint 840 says where they can disagree). Left bridged: `calculated_goods_prices`, `held_goods_prices_in_hours` and
  `partner_own_economy`, which run the price solver over engine state.
- [x] Readers of the views the bridge only re-wrapped read the owners' views: `legacy_dice` and `legacy_act_as` are
  `game_random` and `acting_as`; `nodes_with_mechanic`, `state_military_diffusion`, `partner_reached` and `concern_rows_stopped`
  are read as `mechanic`, `diffusion_index`, `partner_gate_refusal` and `concern_market`.
- [x] Workforce publishes `wage_bill`, `unskilled_trade`, `settlement_tiles`, `labour_need_shares` and `opening_wage_index`
  (`sim/workforce/views_facts.py`). Workforce also publishes `starting_wages` and `wage_schedule_for` (the
  schedule builder is `sim/workforce/wage_schedule.py`).
- [x] Markets publish `material_serves_a_need`, `materials_serving`, `material_substitutes`, `agent_rate`, `agent_credit_room`
  and `agent_economy_opened`; founding a bank is the markets command `FoundBankFromOutside`, so finance no longer holds the
  agent economy.
- [x] Reads that went silently dead when state moved: a `getattr(sim, name, default)` keeps answering its default after
  `name` leaves `Sim`. Found by the full equivalence tier (Rome's army at year 16 granted in full: the bridge's nutrition
  view read `Sim._last_demographic_step`, which demography now holds) and then by checking each defaulted read against a
  built game: the famine cause's food supply (same attribute), the teaching view (`Sim.actors`, gone; actors publish
  `teaching_knowledge`), and a stray `@property` that made the age-at-death read raise TypeError. Still open from the same
  sweep, and the same on the base build: `fuzzy_estimates` reads `viewer_actor_id`, which nothing sets.
- [x] The event-cause evaluator (`event_causes`, `event_cause_state`, `validate_event_causes`) is the hazards module's own and the bridge entry
  `effective_hazard` is deleted. Each cause quantity reads a view of its owner (actors, land, demography, reporting, diffusion), a view answers
  None when the fact is unmeasured, and a relative cause with no start value is not judged instead of reading a start of zero. The divergence
  screen reads the view `event_cause_report`; `validate` calls `sim.hazards.api.cause_check`. Measured with `python3 tools/measure/module_graph.py`:
  77 reads answered by the bridge (78 before), 33 reads of `legacy_*` views (unchanged).
- [ ] Phase 9: replace the remaining defaulted `getattr(sim, ...)` reads with direct reads or views, so a moved field fails
  loudly (`grep -rn 'getattr(sim, "' sim`).
- [ ] The engine bridge answers no module read: each bridged view is published by the module that owns the fact.
- [ ] A width review for each module that depends on more than 15 others, written into its catalogue entry: views that
  mirror methods merged into views that answer questions, sub-domains split out, pass-through dependencies removed,
  and why each remaining edge is needed.

### Phase 7: mods

- [x] Replace the process-global registries of the actors, workforce, polity, demography, agriculture, year phases and stores with per-assembly registrations (extension points; `ModCodeApi` records into the mod's `Operations`).
- [x] The same for the ui's registries: the `interface` module (`sim/interface/`) owns the extension points `interface_commands` and `interface_figures`; the shipped commands and figures (the tables `sim/ui` fills when it loads) and the mods' data are its own provisions, a mod's code provides with `api.command` and `api.figure`, and a word or figure name answered twice is an error naming both owners. A game's table is `command_registry.table_of(sim)` and `figures.figures_of(sim)`; `COMMAND_REGISTRATIONS`, `load_mod_commands` and `register_data_figures` are gone.
- [ ] Rewrite each shipped code mod onto the new interface (one agent per mod).
- [ ] The mod contract stops handing a provider the whole game: the externality, town-size and director-overhead providers receive `provider_game` (read by agriculture, demography and workforce). They receive a declared set of views instead, so a mod's reads appear in the module graph like a module's. `mods/bh_cashshelter_z6f2/hooks.py` still calls `game.state_capacity`, a forwarder that is gone; code mods do not run in the baseline, so no test reaches it.
- [x] Add one SMOKE test per mod operation: replace, remove, add, extend, adjust, provide, withdraw (`sim/tests/test_mod_operations_smoke.py`, three games in one process each).

### Phase 8: kernels

- [ ] Complaint 661: kernels for the largest computations Complaint 497 measures, with the equivalence check as their test fixture.

### Phase 9: finish

- [ ] `python3 -m sim.tests --slow` green.
- [ ] Long equivalence tier and fingerprint against `mr-base`, with every divergence explained by naming its step.
- [ ] Then, and only then, fix the bugs the migration kept on purpose so every step stayed provable (each is a `legacy_*` flag or a Complaint marked "kept until the final equivalence proof"): Complaint 681. Each fix gets its regression test; re-record the baselines after.
- [ ] Baseline ensemble checks.
- [ ] Update `sim/ARCHITECTURE.md`, `PACKAGE_WALLS.md`, CLAUDE.md section 3, and the Complaints this closes (508, 661, and part of 507).
- [ ] Open the single PR (template sections if the repo has one), then subscribe to it.


## Done criteria

Printed by `tools/done_check.sh`: `Sim`'s MRO is only the composition root and defines no rule; money and goods writes only inside their owners; no module imports another's internals; no `register_*` global outside assembly; no `Mixin` in `sim/tests`; shipped mods import only the mod interface; the dependency printout is committed.
