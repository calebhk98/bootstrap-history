# Engine architecture

Read this first to find where code lives and what is safe to change. It describes the engine as it is; it
carries no numbers, because they go stale. Anything that would be a number names the command that measures it
(section 7). The design and its reasons are `docs/architecture/MODULE_REGISTRY_PLAN.md`; per-module detail
(views, commands, state, callers) is in `docs/architecture/catalogue/`, which was written during the move and
lags the code, so re-measure before acting on it.

## 1. The shape

`Sim` (`sim/engine/core.py`) is a composition root. It holds the saved state, the random source, the seat
registry and the year loop, and it builds an **assembly** (`sim/assembly/`) over the modules a game uses. The
rules live in the modules. Each fact has one owner module (`sim/<module>/`); the owner publishes **views** (named
read-only answers) and applies **commands** (typed requests, answered with a result or a refusal with a `cause`,
`sim/refusal.py`). Another module reads only the views it declares and sends only the commands it declares. The
engine bridge (`sim/engine/bridge*.py`) is the thin remainder of reads that still need the engine; the commands
in section 7 report how many are left.

Code that is not yet in a module still calls `Sim` methods that forward to views and commands
(`sim/engine/forward_*.py`, and the properties `core.py` states through `root_facts.py`). Those forwarders are the leftover of the old mixin design and
are being removed; the measure is command 1.

## 2. The assembly (`sim/assembly/`)

| Part | What it does |
|---|---|
| `ModuleSpec` (`spec.py`) | A module's declaration: the state it owns, the views it publishes, the commands it applies, the views it reads and commands it sends, its phases, extension points and kernels. |
| `Assembly` (`assemble.py`, `needs.py`) | Binds every view and command name to exactly one provider and hands each module an object whose attributes are exactly what it declared. An undeclared name is an error naming the module. |
| `views.py`, `clock.py` | A view is stored, derived, keyed or a quote. The clock holds the version counters; a view recomputes only after an input's version moved. |
| `read_guard.py` | In guarded games a view's dict, list or set answer cannot be written through. |
| `slots.py` | Each module's saved state: a world slot and a seat slot per module, built fresh, revived from a save, and rebound on load and seat switch. `act_as` is the one switch of the acting seat. |
| `root_commands.py`, `module.py` | The assembly's own module: the seat registry's facts as views, and the commands the root applies (add a seat, move a seat, reprice the tree). |
| `operations.py`, `mod_access.py` | Mods' operations (add, replace, remove or extend a module, adjust a view, provide to an extension point), applied per game in mod load order, and the `ModAccess` a mod's code is handed in place of the game. |
| `kernels.py` | A module-owned computation a mod may replace by a faster one that reproduces stored samples. |
| `describe.py` | The record a save keeps of which code runs, and the dependency listing. |

The engine chooses the modules in `sim/engine/game_assembly.py`: any `sim/<package>/module_spec.py` lists its
specs in `MODULE_SPECS`. Which module reads and sends what is printed by command 2.

## 3. The modules

One owner per fact. Find a module's views and commands in its `module_spec.py`, and its door in its `api.py`.

| Domain | Modules |
|---|---|
| People and work | `demography` (people by age, region and tile, urban share, food eaten, the farm holding), `workforce` (staff, hours, wages, training, the labour market), `disease` (epidemics and endemic disease), `actors` (the cast of governments, firms, traders and bodies of people beside the seat's households) |
| Money and credit | `ledger` (the one writer of money and goods balances and the tonnes ledger), `finance` (credit, debt, interest, arrears, insolvency, bondage), `coin` (coin as a metal and the price level) |
| Markets and prices | `markets` (the goods market, clearing, household demand, the agent economy), `prices` (calculated price tables, cost books), `foreign_trade` (partner countries and trade with them), `freight` (carriage, routes, carriers) |
| Land and resources | `land` (tile owners, colonies, ways, works, the map), `agriculture` (farmland, weather, soil, wild stock), `resources` (mines, deposits, forest, nitre), `living_stock` (herds), `materials` (supply, demand, the throttle, electricity), `defence_stores` (magazines, garrisons, grain stores) |
| Making things | `production` (what runs, what it earns and costs, industry experience), `projects` (start, progress, completion and failure of projects), `ventures` (the seat's businesses and their plants), `mechanics` (effects the tree's `mechanics` fields add up to) |
| Knowledge | `knowledge` (the tree, what each seat holds, lost, has heard of and can see), `diffusion` (how techniques and literacy spread) |
| State and society | `polity` (standing with society and state, pressure from the state), `hazards` (dated shocks, world hazards, relief, the world event log), `campaigns` (armies, conquest, captives, revolts) |
| Game and play | `seats` (who plays, joining, handover, goals, dealings, sight), `scenario` (the civilisation, the configuration, the year), `reporting` (the seat log, the audit trail), `interface` (the commands and figures a game offers, shipped and from mods), `stores` (mod-declared saved key/value stores), `content` (the mods directory and what installed mods add to the data) |
| Support | `sharing` (answers a view asks many times in a turn, computed once while its inputs stand) |

`sim/economy/`, `sim/agents/`, `sim/labour/`, `sim/geography/` and `sim/ui/` are libraries behind their `api.py`
that the modules above use (`docs/architecture/PACKAGE_WALLS.md`); `sim/world/` holds standalone domain models.

## 4. How a year runs

`Sim.step` runs the ordered phase list in `sim/engine/year_phases.py` (`SHIPPED`, then the mods' phases placed by
their `after` and `before` constraints). A phase is owned by a module (`module_seat_phase`,
`module_world_phase`) or is a short engine step in `year_steps.py`. A **seat** phase runs once per seat inside
`act_as`; adjacent seat phases run together, seat by seat. A **world** phase runs once, with the first seat
acting, and may return the seats still in play; an empty list ends the year. The last phase sends `AdvanceYear`
to the scenario module, which owns the calendar. Read the list in `year_phases.py` for the present order.

## 5. How a game is built and loaded

1. `Sim.__init__` builds the state, then `game_assembly.build` assembles the modules for the game's mods
   directory and mods in load order (`sim/content/`). Assembly order is a pure function of the mod set.
2. The assembly creates one world slot per module and one seat slot per module for each seat
   (`sim/assembly/slots.py`). A module writes only its own slot, and only through its commands.
3. The opening is a series of commands to the owners (scenario, demography, living stock, knowledge, ledger).
4. A save is the state dataclasses' fields (`get_save_fields` in `sim/engine/state.py`, so a new field is saved
   without a list) plus every module's declared slots. Views are never saved. The save records which code ran
   (`describe.record`); a load with a different assembly is refused. There is no migration from an older build
   (CLAUDE.md 4.6).
5. After a load, `game_assembly.attach` rebinds every module to the loaded state.

## 6. Seats and mods

A seat is one player's or actor's own holdings. The seat registry (adding a seat, moving one, the acting seat) is
the assembly's: `Assembly.act_as(seat_id)` is the only switch, and the facts about it are views of the
assembly's own module. `sim/engine/seat_registry.py` holds the functions the root calls. Seat-scoped views are
read for the acting seat. Per-seat module state lives in the seat's slots.

A mod reaches the game through `sim/mod_api.py` (the one `sim` door its Python imports) and the `ModAccess` it
is handed: the views and commands it declared with `api.reads(...)` and `api.sends(...)`. It never receives a
`Sim`. The contract and shipped examples are in `mods/README.md`.

## 7. Measuring the structure

Run from the repository root.

1. `bash tools/done_check.sh` prints the migration's counts: `Sim`'s bases and mixins left, the module graph
   summary, undeclared reads, and writes outside the owners of money.
2. `python3 tools/measure/module_graph.py --modules` prints, per module, the views it reads, the commands it
   sends and how many modules depend on it; without `--modules` only the totals.
3. `python3 tools/check_module_reads.py` lists every view read or command sent that the module's spec does not
   declare (a test host hides these; only a built game fails on them).
4. `python3 tools/check_imports.py` lists imports of modules that do not exist, including lazy ones.
5. `python3 tools/check_ui_views.py` checks every view the UI reads and command it sends exists in a built game;
   `--list` prints the views the UI depends on.
6. `python3 tools/measure/coupling.py` counts references across classes still tied together by inheritance.
7. `python3 -m sim.tests.fingerprint record before.json`, then `check before.json`, proves a refactor changed no
   behaviour. `python3 -m sim.tests.equiv` compares per-year field hashes against a recorded baseline
   (`docs/architecture/baseline/`).
8. `python3 sim/constants.py --burndown` reports declared numbers and temporary heuristics still to derive.
9. `python3 -m sim.tests` (quick tier) and `python3 -m sim.tests --slow` (before a pull request).

## 8. Before you change state

1. Find the owner module of the fact (`sim/<module>/module_spec.py`, or the catalogue file) and change it there.
2. List its readers: grep the view's name, and run command 2. A change to a view's shape is a change to every
   reader.
3. Another module's fact is changed by sending its command, never by writing the field; add the command to the
   owner if none fits, and declare the send in your spec.
4. Do not add a save shim for a renamed field (CLAUDE.md 4.6).
5. For a refactor or speed-up, record a fingerprint first and check it after (command 7). A gameplay change is
   meant to change the simulation; rely on its regression test.

## 9. Known structural problems

- Two owners of prices and traded volumes, the solver and the agent economy:
  `Complaints/507-prices-and-traded-volumes-have-two-owners.md`.
- Temporary heuristics grow faster than they are retired:
  `Complaints/509-temporary-heuristics-grow-faster-than-they-are-retired.md`.
- Tree nodes are both knowledge and concerns:
  `Complaints/510-most-tree-nodes-charge-upkeep-and-make-nothing.md`.
- The forwarders on `Sim` and the mixin fakes in tests are not gone: command 1.
