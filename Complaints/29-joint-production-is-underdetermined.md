# Joint production has no cost-side answer, and never will

**Type:** Modelling limitation, structural
**Priority:** Medium. It cannot be fixed by better data.

Found by `sim/solve_prices.py` while solving the price system for the first
time, and worth recording carefully because it is the first thing this project
has hit that a cost-of-production model **cannot** answer in principle.

## The observation

Five materials converge to the exact same price per physical unit as the
dominant product they come out of, whatever seed the solver starts from:

    silver_kg      out of lead smelting        value share of its batch  0.0%
    platinum_g     out of nickel refining                                3.8%
    germanium_g    out of zinc electrowinning                            2.4%
    indium_g       out of zinc electrowinning                            5.9%
    coal_tar_kg    out of coking                                         4.8%

Silver comes out at 0.203 labour-hours per kilogram. So does lead. Silver is
worth something like a hundred times lead, and the model has no way to know
that.

## Why, and why it is not a bug

One smelt yields two goods. There is one cost and two prices to assign, so
the system is one equation short. The usual fix is net-realisable-value
allocation - split the joint cost in proportion to what each output is worth -
but that needs the prices, which are what we are solving for. It is
self-referential, and the only stable point of that loop is a plain split by
mass.

This is the classical joint-production underdetermination result. It is not a
defect in the data, and no amount of better `yield_basis` writing fixes it: no
fact about smelting galena determines how much of the furnace's cost belongs
to the silver rather than the lead. **The answer genuinely is not in the cost
side.** It is in demand, and demand is not modelled.

## What the solver does about it

Reports it rather than hiding it. Any output holding under half its batch's
converged value is marked `(*)` in all three modes, listed in the header, and
`--why` on one prints the explanation rather than the number alone. The
detection is `minor_joint_byproducts_are_unanchored`.

That is the right behaviour for now: a number presented as derived when it is
an allocation artifact is worse than no number, because the next person builds
on it.

## What would actually fix it

Demand. Once goods have buyers with budgets and preferences, silver has a
price because people want silver, and the joint cost splits against that
rather than against mass. That is the demand side of
`ENDOGENOUS_COSTS_AND_DOMAINS.md` Part 2, and it is a later milestone.

Two cheaper things that are NOT fixes, and should not be mistaken for them:

- **Anchoring silver to its book price.** That reintroduces exactly the
  hardcode the project exists to remove, and worse, it would do so invisibly
  inside a tool whose whole claim is that its numbers are derived.
- **Splitting by a hand-written weight.** Same problem with an extra step.

Leaving it visibly wrong is better than either, until demand exists.

## Scope

Five materials, 16 consumption sites out of 3,596. Small, and unrepresentative
of the rest of the data - almost everything else has a single output and is
unaffected. Recorded because the reasoning generalises: whenever a process
yields more than one thing, the cost side alone cannot price them, and this
project will meet that again in agriculture (grain and straw), in livestock
(meat, milk, hide, tallow) and in refining.

The livestock case is already flagged in `data/production/40_organics.json`,
where hide, bone, fat and bristles carry no share of the animal's grazing
cost, for the same reason.
