# Package walls

The simulator is split into packages that the rest of the code reaches only through a published
surface, so the people working inside one package can change its internals without the others
noticing. `sim/economy/` was the first. `sim/agents/`, `sim/labour/`, `sim/geography/`, `sim/disease/` and `sim/ui/`
follow the same rule.

## The rule

A package is walled when it has an `api.py`. Code outside the package (tests aside) may:

- import only `sim.<package>.api` (or `from sim.<package> import api`), never a submodule;
- read none of the package's private (`_name`) attributes;
- call a package's methods only through its object on `Sim`, `sim.<package>.<method>`
  (`self.labour.wage_bill()`, not `self.wage_bill()`).

Every package also declares `WALL = "two-way"` in its `api.py`: inside it, nothing imports
`sim.engine` or `sim.ui` (the UI may import `sim.engine.ui_port`, its one door), nothing imports
another package except through its `api`, and `Sim` inherits nothing from it. What a package needs
from the engine is handed to it by an engine-side adapter.

Nothing checks these rules automatically: keep to them by review. The packages split from the
engine stay off `sim.economy` too (only `sim/engine/economy_port*.py` may import it, and only `sim.economy.api`);
`sim/tests/test_economy_imports.py` holds that rule for `sim/engine/` only.

## The surfaces

| Package | Import door | Object on `Sim`, and the engine adapter that feeds it |
|---|---|---|
| `sim/economy/` | `sim/economy/api.py`, imported only by `sim/engine/economy_port*.py` | `sim.economy` |
| `sim/labour/` | `sim/labour/api.py` | `sim.labour` (a `Labour`); `LabourWorld` in `sim/engine/labour_port.py`; the labour market every employer asks is `sim.labour.market` |
| `sim/geography/` | `sim/geography/api.py` | `sim.geography` (a `Geography`); `GeographyWorld` in `sim/engine/geography_port.py` |
| `sim/agents/` | `sim/agents/api.py` | none; the engine adapters (`society_actors.py`, `society_disclosure.py`, `interest_groups.py`) consume the api, and `sim/engine/agents_port*.py` (`SimWorld`) is what actors ask of the world (`sim/agents/protocols.py`) |
| `sim/disease/` | `sim/disease/api.py` | `sim/engine/disease_port.py` (the yearly step and the contact heuristic), `sim/engine/validate_disease_data.py` (for `validate`) |
| `sim/ui/` | `sim/ui/api.py` | none; the UI is a consumer and reaches the engine only through `sim/engine/ui_port.py`. `sim/simulator.py` is the entry point |

Each adapter is a plain class (or, for the UI, a module) with one explicit member per thing the
package uses, delegating to the engine. There is no `__getattr__` forwarding (too slow here; see
`HOUSEHOLD_EXTRACTION.md`). A package object is built on first use and cached on the `Sim`; it is
never saved, because the saved state stays in `SimulationState`.

## Extending a surface

When code outside a package needs something new from it:

1. Add the name to the package's `api.py` (for an import) or a public member to the package's
   object (for a question asked of the running simulation).
2. Call it through the door from outside.

When a package needs something new from the engine, add a member to its engine adapter
(`LabourWorld`, `GeographyWorld`, `SimWorld`, `ui_port`) rather than importing the engine.

Do not reach past a surface because it is quicker: a call that needs a package's internals means
the surface is missing a member.

## What still crosses the wall

The walls hold for code: no package imports the engine, and the engine calls packages only
through their surfaces. Two kinds of data still cross:

- **Saved state.** Every package's saved fields still live in `SimulationState`
  (`sim/engine/state.py`), and the engine reads some of them directly, most of all the founder's
  `state.household` record, which carries labour's fields (`employees`, the wage ledgers) beside
  the household's own. Giving each package its own saved state, and routing the engine's reads of
  it through the package, is the next step.
- **Adapter breadth.** `LabourWorld` and `SimWorld` expose many engine members because the
  packages' code reached for many. Each member is a named dependency now, so narrowing them is
  ordinary work inside one package and its adapter.
