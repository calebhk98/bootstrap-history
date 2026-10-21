# Household work is not a need, so there are no servants, cooks or taverns

**Status:** mostly done: the household chooses by the worth of its hour, own hours are kept out of the labour offered, a cohort with no hearth buys cooked food, and a hearth burns cooking fuel; land after the opening (473), a whole-game re-measure and an urban marker remain

Owner decision (530, 2026-10-20): cooking, fetching water and fuel, cleaning, grinding and childcare take hours every
household spends, and they are a need met by the household's own hours or by hiring. Religion as a need is out of scope;
it is a mod (`mods/TASKS.md`).

## What is built

- `data/world/household_work.json`: hours a person's share of household work takes, by task. Water, fuel and grinding
  come from Blackden and Wodon (eds), Gender, Time Use, and Poverty in Sub-Saharan Africa, World Bank Working Paper 73,
  2006, overview p. 9 (opened): an average adult female spends from just under 1 hour to 2 hours 20 minutes a day carrying
  water, firewood and crops for grinding. Cooking, cleaning and childcare hours: no source found, labelled estimates
  (confidence D) with a `retire`. Cooking fuel (`cooking_fuel_mj_per_person_per_day`): Johnson and Bryden 2012 (abstract
  opened).
- `household_work` need in `data/world/needs.json`, no floor, met by `domestic_service_hour`
  (`data/production/95_household_services.json`), made by the `domestic_servant` trade (group `services_state`).
  `cooked_meal_kg` is the cooked food a cook or eating house makes.
- `sim/economy/households_work.py` and `household_work_year.py`: a cohort hires all its household work when an hour of its own
  labour (the wage it faces, averaged over the hours it would sell) is worth more than the servant's price, otherwise none, so
  hiring follows income and the wage with no typed share (the earlier typed budget share is retired). The servant's price is
  last year's `domestic_servant` wage, else the tile's subsistence wage per hour.
- Own hours are kept back: `Economy._shortfall_hours` adds each cohort's own household-work hours to its own-plot hours, so
  `withhold_hours` cuts the offers; `_grow_own` does not count them as spare hours.
- Hearth: a cohort has one when it holds a title or a tenancy on its tile (`has_hearth`). A hearth-less cohort gets
  `without_hearth_basket` (food only from goods marked `ready_to_eat`, no cooking in its household work) and burns no fuel;
  a cohort with one pays the cooking fuel added to its warmth floor (`households_work.with_cooking_fuel`).
- Tests: `sim/tests/test_economy_household_work_year.py`, `sim/tests/test_economy_households_work.py`.

## Still to do

- Land after the opening settles (473), since a new need moves the opening's demand.
- Re-measure with a whole game: the hours kept back are a large share of the offered hours, and the fuel price moves; compare
  `simulator.py economy-check` hired share, wage over floor and fuel prices before and after.
- No urban marker exists in the economy; when one does, it should also remove the hearth.

## Research needed

Cooking, cleaning and childcare hours per person (time-use studies for pre-industrial or subsistence households), which
replace the labelled estimates in `data/world/household_work.json`.
