# Package walls

The simulator is split into packages that the rest of the code reaches only through a published
surface, so the people working inside one package can change its internals without the others
noticing. `sim/economy/` was the first. `sim/agents/`, `sim/labour/`, `sim/geography/` and `sim/ui/`
follow the same rule.

## The rule

A package is walled when it has an `api.py`. Code outside the package (tests aside) may:

- import only `sim.<package>.api` (or `from sim.<package> import api`), never a submodule;
- read none of the package's private (`_name`) attributes;
- call the methods a package's `*Mixin` classes put on `Sim` only through the package's port,
  `sim.<package>.<method>` (`self.labour.wage_bill()`, not `self.wage_bill()`).

`sim/tests/test_package_walls.py` checks all three for every package it finds with an `api.py`,
and keeps the packages split from the engine off `sim.economy` (only `sim/engine/economy_port*.py`
may import it). `sim/tests/test_economy_imports.py` holds the economy's own wall.

## The surfaces

| Package | Import door | Port on `Sim` |
|---|---|---|
| `sim/economy/` | none; the engine reaches it through `sim/engine/economy_port*.py` | `sim.economy` |
| `sim/labour/` | `sim/labour/api.py` | `sim.labour` (`sim/labour/port.py`); the labour market every employer asks is `sim.labour.market` |
| `sim/geography/` | `sim/geography/api.py` | `sim.geography` (`sim/geography/port.py`) |
| `sim/agents/` | `sim/agents/api.py` | none; the engine adapters (`society_actors.py`, `society_disclosure.py`, `interest_groups.py`) consume the api |
| `sim/ui/` | `sim/ui/api.py` | none; the UI is a consumer. `sim/simulator.py` is the entry point |

Each port is a plain class with one explicit member per thing outside code uses, delegating to
the package's implementation. There is no `__getattr__` forwarding (too slow here; see
`HOUSEHOLD_EXTRACTION.md`). A port is built on first use and cached on the `Sim`; it is never saved.

## Extending a surface

When code outside a package needs something new from it:

1. Add the name to the package's `api.py` (for an import) or a member to its port (for a question
   asked of the running simulation). A private name gets a public port member that delegates to it.
2. Call it through the door from outside.
3. Run `python3 -m unittest sim.tests.test_package_walls`.

Do not widen the wall test's exclusions to make a call pass. A test failure means the call should
go through the surface.

## Where this is going

The walls are one-way for now. Outside code sees only the surface, but code inside labour,
geography, agents and ui still reads the `Sim` directly (its mixins run as `Sim` methods, and
`SimWorld` and the UI read `Sim` attributes). The next step makes them two-way, like the economy:
each package stops importing `sim.engine` and gets what it needs from the engine through a
narrow interface handed to it. That means moving labour's fields off `HouseholdState`, moving the
actor state types into `sim/agents/`, and giving the UI an engine-side port of its own.
