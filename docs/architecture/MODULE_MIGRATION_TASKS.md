# Module migration tasks

**Status:** in progress on branch `sim-module-registry-plan`, base `mr-base` = `0be2f72` (a local tag; the code there is identical to the branch head before phase 0). The design is
`MODULE_REGISTRY_PLAN.md`; this file is the execution order and is ticked as each task merges. The work lands as one
pull request when every box is ticked. `main` is frozen for the duration (owner decision 2026-10-25).

Operating rules: only the orchestrating session merges; agents work in worktrees on `mr/<task>` branched from the
integration branch, own named files, never edit `core.py`, `state.py`, `state_seat.py`, `core_seats.py`,
`year_phases.py` or `saveload.py` (they describe the wiring instead), run only targeted topics and the micro
equivalence tier, and hand long runs back. After every merge the orchestrator runs the equivalence tool and the quick
tier, and reverts on red.

## Modules moved

Each row merged with the micro equivalence tier identical to the base and the protocol transcripts unchanged.

| Module | Package | Notes |
|---|---|---|
| ledger (commands side) | `sim/ledger/` | state still in the purses and the tonnes ledger (`legacy_*` views) |
| living stock, defence stores | `sim/living_stock/`, `sim/defence_stores/` | |
| projects (starting) | `sim/projects/` | progress, completion, staffing still mixins |
| coin | `sim/coin/` | carriage is the ledger's `transfer_surcharge` point |
| campaigns | `sim/campaigns/` | |
| reporting | `sim/reporting/` | the seat log and audit trail; world events are hazards' |
| mechanics | `sim/mechanics/` | a query service: many narrow views, no state |
| freight | `sim/freight/` | |
| agriculture | `sim/agriculture/` | the farm holding is demography's |

| foreign trade | `sim/foreign_trade/` | trader cargo legs stay in the agent economy's record until markets moves |
| diffusion | `sim/diffusion/` | literacy, adoption, disclosure |

| knowledge | `sim/knowledge/` | `done`, `granted`, `done_year`, `revealed` stay in the engine behind `legacy_*` (many writers); Complaint 735 |
| resources | `sim/resources/` | mines, deposits, forest, nitre beds; Complaint 730 |

| hazards | `sim/hazards/` | dated shocks, world hazards, relief, the world event log, the output factor; Complaints 740, 741 |
| materials | `sim/materials/` | supply, demand, the throttle (a pure quote plus `ApplyThrottle`), electricity, project materials |

Full equivalence tier identical at the knowledge merge (`877cff82`). Micro and stress tiers identical at `c4ed5848`.

| seats | `sim/seats/` | joining, ending, handover, sight, dealings, goals and win conditions, founder death (`EndRun`); the registry and `act_as` stay on `Sim` |

| prices | `sim/prices/` | the price solver's callers read quotes; the spin-up cache follows modules named in `DISCOVERS` |
| polity | `sim/polity/` | standing, state notice, demands, patronage, the society's value weights; Complaint 760 |
| disease | `sim/disease/` | the epidemic year runs inside demography's regional step, as two commands around the externality door |

| demography | `sim/demography/` | the three age bands, regions, urban share, food eaten, the farm holding; the age bands are the only copy (no `Sim.population` mirror) |

| actors | `sim/actors/` | the cast, its records and the actors' world (was the engine's `agents_port*`); `state.actors` is a property over the slot |

| workforce (partly) | `sim/workforce/` | the labour package behind `WorkforceWorld`, its commands and phases; still to do: the staff and hour fields on the household record become its seat state, and its `legacy_state` and `legacy_game` reads go; Complaint 762 |

| land | `sim/land/` | the owner map, colonies, the map and geography handles; still to do: `improvements`, `ways_under_construction`, `works`, `works_under_construction` and `ways.py` (with transport and works) |

| markets (partly) | `sim/markets/` | the market book, flows, clearing, goods categories, household demand ratios; still to do: the goods market object and the economy port (`Sim.economy`, `Sim.goods_market`, `economy_port*.py`), reached today through `legacy_game` |

| finance | `sim/finance/` | credit limit, interest and arrears, insolvency, debt bondage, purchases and affordability, the seat bank; the agent economy's own credit and bank files in `sim/economy/` stay behind its api; Complaint 763 |

In progress: workforce state. `stores` (mod stores) is a framework service and moves with phase 7. Next: the rest of markets (the goods market object and the economy port); then finance, production, ventures, the rest of projects.

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

### Phase 7: mods

- [ ] Replace the 12 process-global registries in `mod_code.py` and the packages with per-assembly registrations under one clash rule.
- [ ] Rewrite each shipped code mod onto the new interface (one agent per mod).
- [ ] Add one SMOKE test per mod operation: replace, remove, add, extend, adjust, provide.

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
