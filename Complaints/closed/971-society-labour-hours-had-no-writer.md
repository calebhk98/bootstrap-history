# The society's labour hours by trade had no writer, so gathering caps and the hours table read zero

**Status:** closed - the figure is worked out from the labour core's people and a person-year's hours; the dead field is gone

`society_labour_hours` (trade to hours the society's workers give in a year) was a field of `WorkforceSociety` that
nothing in non-test code wrote after the central workforce allocation was removed (the allocation that set it,
`society_hours(total_hours, farm_hours, shares)` called from `_allocate_farm_workforce`, is present in the 2026-10-31
root commit 6afdb343 and absent by 2026-11-03; the history there is grafted, so no single diff shows the deletion).
Readers kept reading the empty dict:

- `food_potential` -> `_gathering_caps` -> `hours_cap_kcal`: every food source a gathering trade names got a cap of
  zero, so hunted, gathered and fished kcal were capped to zero (`capped_kcal` takes `min(kcal, cap)`).
- `occupation_hours_by_trade` (`economy-check --occupations`): the "by hours worked" table printed 0.0% for every
  group on a 3-year Rome game.
- `Allocation.farm_share_of_hours` fell back to the head count, so it was right by accident; `_non_farm_need_shares`
  returned no shares when the recipe graph gave none.

Fix: `sim/labour/society_hours.py` `society_hours_by_trade(people_by_trade, hours_per_person_year)` (people times the
hours a person-year counts, empty while the agent economy opens). The workforce module's `society_labour_hours` view,
`occupation_hours_by_trade` and the labour world's `society` reader all compute it from the declared
`agent_people_by_trade` and `agent_working_hours` views. The stored field and its equivalence-table row are deleted.
Regression test: `sim/tests/test_society_hours_by_trade.py`.

On a game (`python3 sim/simulator.py economy-check --occupations --years 3 --civs rome_100ad`) the shares by hours are no
longer zero, and they equal the shares by people: every person counts one person-year, so nothing yet holds the hours a
trade's people actually worked. That limit is what the table can show, not a defect of this fix.
