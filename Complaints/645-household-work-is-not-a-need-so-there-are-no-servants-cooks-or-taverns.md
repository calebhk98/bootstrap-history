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
- Own hours are kept back: `labour_supply.HourSupply` (earlier `Economy._shortfall_hours`) adds each cohort's own household-work hours to its own-plot hours, so
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

Done in part. The hours in `data/world/household_work.json` now come from opened sources, per adult woman: water, fuel and
grinding from a rural Burkina Faso time allocation table (Carr and Sandhu 1988, as reproduced in Gordon, Swetman and Albright,
Issues Paper 6, 2002, Box 1); cooking, cleaning, laundry and care from the Ghana 2009 time-use diary (Dinkelman and Ngai, JEP
36(1), 2022, Online Data Appendix, Table A.1). Both are confidence C. What is still open:

- The share of adult women among a household's people is still a labelled estimate (confidence D); every task multiplies by it.
- The Ghana diary is a national sample with some piped water and mills, not a pure subsistence household, and its cooking
  category includes some wood and water fetching that the first task also counts. A time allocation study of a society
  without either (Minge-Klevana 1980, the UCLA Time Allocation project) was not found open online.
- The Burkina Faso table is a secondary reproduction with no survey year or sample size, and its "Household" line (cooking
  among it) is not broken down.
- Servants per household (the historical servant literature) was not searched; the hire switch rests on wages, not on a count.

## Update: household work shares the choice

Household work's own hours and the hours kept for the plot are the same kind of choice (an hour at home against the wage).
`HourSupply` keeps the larger of the plan and the plot choice, then adds household work. The fixture has no
household-work data, so only the plot side is exercised there; leisure is not modelled.

## Update: leisure is modelled, household work still enters at the servant's price (473 Update 8)

A household's hours are shared by `labour_supply.HourSupply`: own-plot plan and household work first (the work still hired or done
by the all-or-nothing rule against the servant's wage), then the plot by its marginal return, then leisure by a declared
preference (675), then sale. At the opening the leisure anchor is solved so offered equals hired, so what household work and
leisure each take of Rome's 2000 hours a worker is still not measured separately: Rome's household-work hours come from the data
file's estimates (cooking, cleaning and childcare confidence D) and are not re-measured here. The hire/own switch is still a
step in the wage (households differ in the wage they face, so the aggregate rises step by step); it was not made smooth.
Cooked food, cleaning and childcare as bought substitutes are not yet data in `household_work.json`.

## Effect measured after the sourced hours (PM)

The opening's typical traded good now sells below its making cost (`price_over_making_cost_band_validation`, see 558): the
stationary opening (473) does not yet take the larger household day out of the hours it plans with. The figures stay; the
opening is what has to read them.
