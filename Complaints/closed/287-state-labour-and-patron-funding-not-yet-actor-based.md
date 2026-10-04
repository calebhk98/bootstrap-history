# The state's soldiers are not a trade, and patron funding still ignores the treasury

**Status:** closed - items 1 and 2 built earlier; item 3 was already built when re-measured (see the last note). What is left of the military share as a basis for equipment is 330.

Three things the state budget does not do yet, each measurable.

1. **Soldiers are not a trade in the labour market.** The state's staff enter the founder's labour pool through `BudgetView.local_staff`: the share of the nation's people of that trade the state employs, applied to the pool the founder can reach. There is no soldier trade, so the army is booked as `labourer` against the whole working age. Drawing the national army from the hired-labourer trade in proportion to the nation's labourers (a few tens of thousands) would take the whole local pool. Soldiers pulled out of production do not lower national output or raise the unskilled wage either, because `society_output` reads the working age unchanged.
2. **Patron funding is still `state_funding`.** `Sim.state_funding` (`economy_production.py`) is a formula (`STATE_FUNDING_BASE` and two siblings, all labelled heuristics) that adds money to the founder's revenue from nowhere. It should be a payment from the treasury, bounded by its purse and its spending priorities, so a state in deficit funds nobody. Increment 5.
3. **The state's adoption is a half-life curve.** `state_military_diffusion` still reads `DIFFUSION_HALF_LIFE_MILITARY_YEARS`, not what the government actor holds; the budget reads it (through `BudgetView.equipment_kg_per_soldier`) to scale equipment. Increment 3.

Check 3 with `grep -rn "state_military_diffusion" sim --include=*.py`.

Done: item 2. `Sim.state_funding` is what the treasury paid (`Government.pay_patron`, from the purse after the standing need, nothing when any need went unpaid); the old formula survives as `patron_funding_ask`, a labelled heuristic for what a patron would give. Item 1 in part: `society_output` excludes soldiers under arms, so a larger army lowers revenue; the trade itself and the wage are 314. Item 3 is untouched.

Update: item 1 is built (314): the army is booked in the `soldier` trade, drawn from the working age through the one labour market. What is left is item 3 only: `grep -rn "state_military_diffusion" sim --include=*.py`.

Update (item 3, re-measured): no half-life curve for the state remains. `grep -rn "HALF_LIFE_MILITARY" sim --include=*.py` finds nothing; `civ_diffusion` returns 1 for a military node the government holds (`state_treasury().knowledge`) and 0 otherwise, `state_military_diffusion` is the share of the founder's military nodes it holds, and the war relief counts the weapons it holds. The curve carries nothing the government's own copies do not already decide: whether the state adopts is its purse, its policy's worth for the node and the copy's work and risk, all in `Government`. The calendar plays no part (`sim/tests/test_invention_disclosure.py` increment 3: two centuries after the founder's invention the state holds nothing; adoption rises only as the government's knowledge does; `sim/tests/test_state_weapon_relief.py` for the relief). The actor is never absent (`state_treasury()` creates it), so no fallback is kept. The remaining oddity, that the share falls as the founder invents more weapons, is 330.
