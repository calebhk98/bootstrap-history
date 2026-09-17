# `solve_prices.py` rejects every recipe cycle, including the one its own docstring uses as the example

**Type:** Tooling / modelling
**Priority:** Medium. It does not bite today; it blocks the next physically-correct thing anyone tries to model.

## What the docstring says

`sim/solve_prices.py`, module docstring:

> **CYCLES ARE EXPECTED.** Iron needs charcoal; charcoal needs timber and
> labour; an axe needs an iron edge. That is a cycle in the recipe graph and
> the fixed-point iteration handles it the same way it handles everything
> else - by converging to the prices where the equations agree, not by
> requiring the graph to be acyclic.

## What the code does

`compute_resolvable_materials` grows a set by repeated passes, adding a
recipe's outputs only when **every** one of its inputs is already in the set.
That is a topological-order construction. A cycle never enters it, by
construction, and neither does anything downstream of a cycle. The numeric
iteration below it is never reached, because a material that is not
resolvable is reported as having no path to a price.

Demonstrated on the docstring's own example - timber extracted, iron needing
timber and an axe, an axe needing iron:

```
entries = {
  "timber": outputs timber_m3 1.0,  inputs {},                          labour 2.0
  "iron":   outputs iron_kg 10.0,   inputs timber_m3 1.0, axe_each 0.01, labour 5.0
  "axe":    outputs axe_each 1.0,   inputs iron_kg 2.0,                  labour 3.0
}

compute_resolvable_materials(...) -> {'timber_m3'}
```

Iron and the axe are both reported unresolvable. They are not: this system is
productive - 0.01 axes per 10 kg of iron and 2 kg of iron per axe is a tiny
circulating share, the fixed point exists, and the damped Jacobi iteration
already in the file would find it.

A self-input is the degenerate case of the same thing, and it is worse,
because it poisons everything downstream:

```
wheat: outputs wheat_kg 742.5, inputs wheat_kg 165.0 (seed corn), labour 150
bread: outputs bread_kg 1.0,   inputs wheat_kg 1.3,               labour 0.2

compute_resolvable_materials(...) -> set()     # wheat AND bread
```

## Why it matters, given that nothing is currently unresolvable

The solver today reports `179 of 179 referenced materials have a path to a
price, 0 with NO path`. The dataset happens to be acyclic. So this is latent -
and latent in a way that pushes the data away from physical truth, which is
the part that matters:

- **Seed corn is a real input to wheat.** The physically right entry for
  `wheat_kg` lists 165 kg/ha of wheat among its own inputs and outputs the
  gross 742.5 kg/ha. It cannot be written that way while this holds, so
  `data/production/40_organics.json` nets the seed out and outputs 577.5
  instead, and says so. That netting hides a mechanism that should be
  visible: seed corn is a first claim on the harvest, and a famine that eats
  next year's seed is a real and well-attested way a population falls further
  than the bad harvest alone explains. You cannot model that against a
  net-of-seed yield.
- **Tools that make tools are the same shape.** An axe felling the timber
  that fires the furnace that makes the axe is not an exotic case; it is what
  an economy is. Every step toward endogenous capital (the field
  `data/production/_SCHEMA.md` records as NOT EXISTING) walks into this.

## Why the fix is not "iterate anyway"

The strict pass exists for a good reason, stated in the same docstring: a
damped iteration will hand back a converged-looking float for a material
stuck in a cycle that never touches labour or an extracted good, and
floating-point arithmetic cannot tell that apart from a real answer. Deleting
the pass would trade a false negative for a false positive, which is worse.

The right rule is the productiveness condition, not reachability. A set of
recipes prices out if the input-output matrix restricted to it has spectral
radius below 1 - equivalently (Hawkins-Simon), if running the system
end-to-end yields more of every good than it consumes. A cycle that consumes
0.01 axes to make what builds 0.5 axes is productive; a cycle that consumes
more of itself than it makes is not, and that is the case the current pass is
right to refuse.

A cheaper implementation that gets most of it: find strongly connected
components, treat a component as resolvable when every input from OUTSIDE the
component is resolvable AND the iteration restricted to the component
converges (spectral radius under 1 shows up directly as the iteration
contracting rather than growing). Report a non-contracting component by name,
as the current pass reports a missing path.

## Test

`sim/tests/test_price_solver_cycles.py` asserts both cases above. It fails
today, which is the point - see its own docstring for why it is written as an
expected failure that must be converted, not deleted, when the pass is fixed.


---

## FIXED

`compute_resolvable_materials` now runs the topological pass first, then
decomposes whatever it could not reach into strongly connected components
and tests each one for PRODUCTIVENESS rather than reachability: it runs the
real damped-Jacobi machinery restricted to the component, with external
materials pinned, and accepts the component only if that iteration
contracts. Pinning the externals at a placeholder is valid because the
contraction of an affine map does not depend on its constant term.

The strict half survives, which was the requirement. A component whose
prices grow without bound is refused and NAMED, and so is one with no
anchor - no path to labour or to an already-resolved material. Both are
reported under "UNPRODUCTIVE CYCLES" rather than silently dropped.

On this file's own two reproductions:

    axe/iron/timber      {'timber_m3'}  ->  {'timber_m3', 'iron_kg', 'axe_each'}
    seed corn + bread    set()          ->  {'wheat_kg', 'bread_kg'}

`sim/tests/test_price_solver_cycles.py` was inverted rather than deleted, as
its own docstring instructed, and gained two cases for the refusals that
must still happen: a recipe consuming 1.5 kg of itself per kg produced
(spectral radius at or above 1), and a pure self-loop with no labour and no
external input.

## The prediction in this file came true within the hour

It said fixing this was a prerequisite for capital, because `iron_bar_kg`'s
capital entry lists iron bar among its build materials and `pig_iron_kg`'s
lining lists iron bar while iron bar is made from pig iron. When capital was
wired into the solver, feeding `build_materials` into the resolvability
graph exposed exactly that two-cycle. It resolves cleanly, no diagnostic
fires, and the run still reports 179 of 179 priced.

Seed corn remains netted out in `data/production/40_organics.json` for now.
The blocker is gone, so writing it as the physical input it is - gross yield
742.5 kg/ha with 165 kg/ha of wheat among its own inputs - is now possible
and is a separate, behaviour-changing commit.
