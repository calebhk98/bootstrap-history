# The Norse start cannot feed its people from its cleared land, so the opening puts every hour on the farm

**Status:** closed (opening area); herd, dairy and fish food still absent from the food balance (see Resolution)

Found rewriting `workforce_spinup` (640). At the Norse opening the food balance asks for more farm workers than the
civilisation has people of working age: the cleared land, cropped in the declared rotation, cannot feed the declared
population, so `current_farm_hours` (`sim/labour/labour_allocation.py`) caps the opening at all the hours and no other
trade gets any. The rule behaves as written; the initial conditions disagree with each other.

Measure: `current_farm_hours` and `farm_workers_needed` on the `norse_900ad` setup (the test
`sim/tests/test_workforce_spinup.py` names the case), against the civilisation's working-age people.

Why it matters: a start whose land cannot feed its people opens in famine whatever the player does, and its non-farm
economy is empty (CLAUDE.md 4.2). The Norse also lived on herds, fish and dairy, which the farm balance may not count.

What it would take: check the Norse cleared land, rotation and population against sources, and whether pasture, herd
and fish food (532, 615) enter the food balance; fix the data or the balance, not the cap.

## Resolution

Cause: the opening cleared area was sized for the people at reference soil (`farmland_for_population`) and only
capped by the ground held, so land with a yield factor below the reference (the Norse tiles) fed fewer people than the
sizing assumed, and the baseline farm need exceeded the working-age people. Fix: `agriculture_labour.hectares_netting_reference_food`
sizes the area down the best-first ladder of the held tiles so it nets as much food after seed as the reference area
would (seed is sown on every hectare, so poor ground needs more than the yield ratio); the engine and the country
farms (`sim/agents/country_farm.py`) pass the ladder. Rule tests: `OpeningAreaTests` in `sim/tests/test_farm_clearing.py`.
Measure: the baseline farm workers of `_expected_year_farm_need` on the Norse opening against `population.working_age`.
Not done: pastoral, dairy and fish food (532, 615) still do not enter the food balance, so the Norse farm still carries
a large share of the working-age people; that is those complaints' work, and no source for Norse diet shares was opened here.
