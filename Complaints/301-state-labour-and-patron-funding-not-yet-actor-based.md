# The state's soldiers are not a trade, and patron funding still ignores the treasury

**Status:** open - found while building 109; remains of ACTORS_NEXT increments 3 and 5

Three things the state budget does not do yet, each measurable.

1. **Soldiers are not a trade in the labour market.** The state's staff enter the founder's labour pool through `BudgetView.local_staff`: the share of the nation's people of that trade the state employs, applied to the pool the founder can reach. There is no soldier trade, so the army is booked as `labourer` against the whole working age. Drawing the national army from the hired-labourer trade in proportion to the nation's labourers (a few tens of thousands) would take the whole local pool. Soldiers pulled out of production do not lower national output or raise the unskilled wage either, because `society_output` reads the working age unchanged.
2. **Patron funding is still `state_funding`.** `Sim.state_funding` (`economy_production.py`) is a formula (`STATE_FUNDING_BASE` and two siblings, all labelled heuristics) that adds money to the founder's revenue from nowhere. It should be a payment from the treasury, bounded by its purse and its spending priorities, so a state in deficit funds nobody. Increment 5.
3. **The state's adoption is a half-life curve.** `state_military_diffusion` still reads `DIFFUSION_HALF_LIFE_MILITARY_YEARS`, not what the government actor holds; the budget reads it (through `BudgetView.equipment_kg_per_soldier`) to scale equipment. Increment 3.

Check 3 with `grep -rn "state_military_diffusion" sim --include=*.py`.
