# Package walls

The simulator is split into packages that the rest of the code reaches only through a published
surface, so the people working inside one package can change its internals without the others
noticing. There are two kinds of package under `sim/`:

- **Modules** (`sim/<module>/`, each with a `module_spec.py`): the owner of a fact. Modules reach each
  other only through views (named read-only answers) and commands (typed requests to the owner), each
  declared in the module's spec. The list is in `sim/ARCHITECTURE.md` section 3; the design is
  `MODULE_REGISTRY_PLAN.md`. A module's `api.py` is its door for what other code may import: its command
  classes, constants and pure rules, never its state.
- **Libraries** (`sim/economy/`, `sim/agents/`, `sim/labour/`, `sim/geography/`, `sim/ui/`): behind an
  `api.py`, used by the modules that wrap them.

## The rule

A package is walled when it has an `api.py`. Code outside the package (tests aside) may:

- import only `sim.<package>.api` (or `from sim.<package> import api`), never a submodule;
- read none of the package's private (`_name`) attributes;
- read another module's facts only through a view declared in its own spec, and change them only by a
  command declared in its own spec. There is no `sim.<module>` object to call into.

Every `api.py` declares `WALL = "two-way"`: inside the package nothing imports `sim.engine` (the
comment beside `WALL` names the one exception where there is one), and `Sim` inherits nothing from it.
What a library needs from the game is handed to it by the module that wraps it, as plain data or a small
world object (the table below).

`python3 tools/check_imports.py` finds imports of modules that do not exist. `python3 tools/check_module_reads.py`
finds a module reading a view or sending a command that its spec does not declare. `python3 tools/measure/module_graph.py`
prints the module dependency totals, including reads still answered by the engine bridge.
Nothing checks the import rule above automatically: keep to it by review.

## The surfaces

| Package | Import door | Who hands it the game |
|---|---|---|
| `sim/economy/` | `sim/economy/api.py`, imported by the `markets` module (`sim/markets/port*.py`) and `sim/engine/economy_port_effects.py` | the `markets` module builds the agent economy and the goods market; they read the game through `PortWorld` (`sim/markets/port_world.py`) |
| `sim/labour/` | `sim/labour/api.py` | the `workforce` module (`sim/workforce/module.py`) holds the `Labour` this package implements; `WorkforceWorld` (`sim/workforce/world.py`) answers what labour reads of the game from the module's declared views |
| `sim/geography/` | `sim/geography/api.py` | the `land` module (`sim/land/`) holds the `Geography` and answers its reads (`sim/land/map_views.py`) |
| `sim/agents/` | `sim/agents/api.py` | the `actors` module (`sim/actors/`) is the actors' world (`sim/actors/world*.py`, `sim/agents/protocols.py` lists what actors ask of it) |
| `sim/disease/` | `sim/disease/api.py` | the `disease` module (`sim/disease/module.py`): the yearly step and the contact heuristic, reading the game through its declared views; `sim/agents/country_disease.py` runs foreign countries' disease |
| `sim/ui/` | `sim/ui/api.py` | the UI reads views and sends commands through `sim/engine/ui_port.py`; `tools/check_ui_views.py` checks every name it uses exists. `sim/simulator.py` is the entry point |
| `sim/content/` | `sim/content/api.py` | the `content` module: the mod loader (manifests, ids, removals, civilisations, world data, constants), the tree's field defaults and the household need data. The engine, the UI and the tests import it; it imports nothing from the engine |
| `sim/mod_api.py` | the one `sim` import a mod's Python may make | the game hands a mod a `ModAccess` holding only the views and commands it declared (`sim/assembly/mod_access.py`) |

A library object is built when its module is assembled and is never saved, because saved state is held
in the modules' slots and `SimulationState`. There is no `__getattr__` forwarding (too slow here; see
`HOUSEHOLD_EXTRACTION.md`).

## Extending a surface

When code outside a package needs something new from it:

1. For a fact another module owns, add a view (a read) or a command (a change) to the owner's spec and
   declare it in the reader's or sender's spec. For an import, add the name to the package's `api.py`.
2. Use it through the declared door from outside.

When a library needs something new from the game, add a member to the world object its module hands it
(`WorkforceWorld`, `PortWorld`, the actors' world, `ui_port`) backed by a declared view, rather than
importing the engine.

Do not reach past a surface because it is quicker: a call that needs a package's internals means the
surface is missing a member.

## What still crosses the wall

- **The engine bridge.** Reads a module still needs from the engine are published by `sim/engine/bridge*.py`;
  `python3 tools/measure/module_graph.py` prints how many remain (it counts reads answered by the bridge).
- **Forwarders on `Sim`.** Engine, mod and test code that is not yet in a module still calls `Sim` methods
  that forward to views (`sim/engine/forward_*.py`); `bash tools/done_check.sh` prints how many bases remain.
- **Adapter breadth.** `WorkforceWorld`, `PortWorld` and the actors' world expose many members because the
  packages' code reached for many. Each member is a named dependency, so narrowing them is ordinary work
  inside one module.
