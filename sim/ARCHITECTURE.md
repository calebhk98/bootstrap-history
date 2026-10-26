# Engine architecture

Read this first to find where code lives and what is safe to change. It
describes the engine as it is; it carries no numbers, because they go stale.
Anything that would be a number names the command that measures it (section 6).

## 1. What `Sim` is

`Sim` (`sim/engine/core.py`) is one object composed of many mixins. Its base
list in `core.py` is the authoritative list of mixins; each is a class in its
own `sim/engine/` module and talks to the others through `self`. The split
removed merge conflicts, not coupling: any method can read or write any field.

State lives in `SimulationState` (`sim/engine/state.py`) and, for one player's
own holdings, in a seat (`state_seat.py`). `ForwardingPropertiesMixin`
(`core_properties.py`) keeps the older flat names (`sim.capital`) working by
forwarding to the owning subobject (`sim.state.household`); both spellings
reach the same value.

Measure its shape (base count, MRO size, method count): command 1 in section 6.

## 2. Map of `sim/engine/`

Find a group with `ls sim/engine/<prefix>*`. Command 2 prints every module's
docstring first line.

| Topic | Prefixes and files |
|---|---|
| Step phases (what one year does, in order) | `core_step_phases`, `step_phase_*`, `year_run` |
| Projects (start, progress, finish, staffing) | `projects*`, `project_materials`, `blockers`, `failure_*`, `planner`, `path_search` |
| Seats and the founder | `core_seats`, `seat_*`, `state_seat`, `state_holdings`, `state_demand`, `founder_sales`, `cash_*`, `goals`, `fog` |
| Markets and prices | `prices`, `solve_prices*`, `making_cost`, `long_run_costs`, `rent_standin`, `solve_cache`, `goods_market_*`, `market_*`, `incumbent_prices`, `producer_costs`, `entry_cost`, `wage_*`, `money_units`, `real_*` |
| Node money (revenue, upkeep, capital) | `node_*`, `industry_*`, `concern_*` |
| Foreign trade, freight, coin | `foreign_*`, `trader_cargo`, `sim/freight/` (the freight module), `sim/coin/` |
| Economy port | `economy_port*`; older money, credit, mining and goods code is `economy_*` |
| Workforce (labour) | `sim/workforce/` (the module), `bridge_workforce`, `forward_workforce`, `projects_staffing*` |
| Geography port | `geography_port`, `ways`, `works`, `held_works`, `colonies`, `mine_deposits` |
| Society and groups | `society*`, `interest_groups`, `legitimacy`, `benefactions`, `visibility` (hazards are `sim/hazards/`) |
| Geography port | `geography_port`, `ways`, `works`, `held_works`, `colonies` |
| Living stock | `living_stock*`, `food_relief`, `defence_stores` |
| Mods | `mods*`, `mod_*`, `actor_kinds_data` |
| Data loading and validation | `data`, `tree_source`, `tree_merge`, `catalog`, `validate_*`, `*_check` |
| Saving and loading | `saveload`, `save_companions`, `settings*`, `shipped_openings*`, `identity_cache` |
| Units and display helpers | `units*`, `readable`, `ui_data`, `ui_commands` |

## 3. Ports

The walled packages (`sim/economy/`, `sim/agents/`, `sim/labour/`,
`sim/geography/`, `sim/ui/`) and the disease package are reached only through
their `api.py`; the rule and how to extend a surface are in
`docs/architecture/PACKAGE_WALLS.md`. The engine's side of each wall is a port
module in `sim/engine/`:

| Wall | Engine side |
|---|---|
| Economy | `economy_port.py` (the one door) and its parts `economy_port_*.py` |
| Labour | `sim/workforce/world.py` (its views) and `bridge_workforce.py` |
| Geography | `geography_port.py` |
| Agents | the actors module's world, `sim/actors/world.py` and its views `world_*.py` |
| UI | `ui_port.py` (re-exports the engine names the UI uses) |
| Disease | `disease_port.py` |

A walled package does not reach into the engine; it asks through the port,
which hands over what it needs.

## 4. Known structural problems

- Two owners of prices and traded volumes, the solver and the agent economy:
  `Complaints/507-prices-and-traded-volumes-have-two-owners.md`.
- No wall around engine state, so a change cannot see its readers:
  `Complaints/508-the-engine-has-no-wall-and-sim-state-has-no-owner.md`. To
  find every reader of a field, run commands 3 and 4 in section 6 and read
  `core_properties.py` for the field's second name.
- Temporary heuristics grow faster than they are retired:
  `Complaints/509-temporary-heuristics-grow-faster-than-they-are-retired.md`.
- Tree nodes are both knowledge and concerns:
  `Complaints/510-most-tree-nodes-charge-upkeep-and-make-nothing.md`.

## 5. Before you change engine state

1. Grep readers and writers of the field (commands 3 and 4, plus
   `grep -rn "\.field_name\b" sim --include=*.py`); include `sim/tests/`.
2. Check `core_properties.py` for a forwarding property: the field may also be
   reached under another name.
3. Check whether `ui_port.py` or an `agents_port_*.py` view re-exports it.
4. Do not add a save shim for a renamed field (CLAUDE.md 4.6).
5. For a refactor or speed-up, record a fingerprint first and check it after
   (command 5). A gameplay change is meant to change the simulation; rely on
   its regression test instead.

## 6. Commands

Run from the repository root.

1. `python3 -c "from sim.engine.core import Sim; print(len(Sim.__bases__), len(Sim.__mro__), sum(callable(getattr(Sim,n,None)) for n in dir(Sim)))"` prints base count, MRO size, callable attribute count.
2. `python3 -c "import ast,glob,os; [print(os.path.basename(f)[:-3], '|', (ast.get_docstring(ast.parse(open(f).read())) or '').split('\n')[0]) for f in sorted(glob.glob('sim/engine/*.py'))]"` prints each engine module and its docstring's first line.
3. `grep -rlE "(self|sim)\.nodes\b" sim/engine sim/ui sim/agents --include=*.py` lists files that read a field (here `nodes`; substitute yours).
4. `grep -rnE "\bsim\.[a-z_]+ = " sim/ui sim/agents sim/economy sim/labour --include=*.py` lists assignments to `Sim` fields from outside the engine.
5. `python3 -m sim.tests.fingerprint record before.json`, then `python3 -m sim.tests.fingerprint check before.json`.
6. `python3 sim/constants.py --burndown` reports declared numbers and temporary heuristics still to derive.
7. `python3 -m sim.engine.validate_unlinked_producers` lists nodes with upkeep that run no production entry (Complaint 510).
8. `python3 -m sim.tests` (quick tier) and `python3 -m sim.tests --slow` (before a pull request).
