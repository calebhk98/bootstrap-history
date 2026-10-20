# The Norse start cannot feed its people from its cleared land, so the opening puts every hour on the farm

**Status:** open

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
