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

---

## Resolved, by the route this file predicted

This complaint said the answer "genuinely is not in the cost side. It is in
demand, and demand is not modelled." `sim/world/demand.py` now models it,
and the lead/silver case comes out:

```
recipe outputs: lead_kg 1000.0, silver_kg 0.46
mass shares:    lead_kg 99.9540%   silver_kg  0.0460%
value shares:   lead_kg  0.8213%   silver_kg 99.1787%
```

A complete reversal. Silver is 0.046% of the batch by mass and carries 99.2%
of its value, which is the whole point: no fact about smelting galena could
ever have produced that, and a mass split never will.

## How the circularity was broken

The complaint's own objection was that net-realisable-value allocation needs
the prices, which are what we are solving for. The escape is that **a joint
by-product's quantity is fixed for the period** - you get 0.46 kg of silver
per tonne of lead whatever you think silver is worth. That is Marshall's
market-day case, and with supply vertical the price that clears aggregate
household demand against it has a closed form. It is demand-determined and
owes nothing to what lead "should" cost, so there is no loop to close.

The value share then falls out as price times quantity, normalised.

## The number is still wrong, and the decomposition says where

Derived silver:lead ratio is 262,515x against the ~100x this project used as
its target. Do not read that as the mechanism failing; read the two halves:

    silver   36,513 h/kg derived   vs  4,227 h/kg book-implied   ~8.6x high
    lead      0.1391 h/kg derived  vs      8.0 h/kg book-implied  ~57x low

A demand-only mechanism landing within an order of magnitude of silver's
real price is a good result. Almost the entire ratio error is LEAD being too
cheap, which is the missing land rent `Complaints/32` already diagnosed on
the cost side - not a defect in this mechanism.

## And the target itself is not a clean comparator

`silver_kg`'s book price is DEFINITIONAL: one denarius was 3.15 g of fine
silver, so the book number is the definition of the currency rather than an
observed price. Validating a derived silver price against it is close to
circular, and the book's own implied ratio is 528x, not the ~100x the target
states. Both numbers deserve less weight than they were being given.

## What stays true from the original complaint

The two things it warned against are still wrong and are still not done:
anchoring silver to its book price, and splitting by a hand-written weight.
Neither was needed. The solver's `(*)` marking for unanchored minor
byproducts should stay until demand is wired into `sim/solve_prices.py`,
which has not happened - `demand.py` is standalone, like everything else
under `sim/world/`.
