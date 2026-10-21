# Household work is not a need, so there are no servants, cooks or taverns

**Status:** mostly done: the household chooses by the worth of its hour, own hours are kept out of the labour offered, and a cohort with no hearth buys cooked food; fuel at the hearth and land after the opening (473) remain

Owner decision (530, 2026-10-20). Cooking, fetching water and fuel, cleaning, grinding and childcare take hours every
household spends. Nothing in `data/world/needs.json` or the household model books them, so domestic service, cooks and
tavern keepers have no demand, and their hours sit in the generic `labourer` pool (619).

What it would take: a household-work need met by the household's own hours or by hiring, the same choice as own-plot
growing (`sim/economy/households_own.py`), so a richer household hires more as its own hours are worth more. Cooking
needs a hearth and fuel; a household without one (urban tenancy, 551's endowments) buys cooked food, which is the
demand for cooks and taverns. The hours a household needs come from a source (time-use studies), not a typed share.
Land after the opening settles (473), since a new need moves the opening's demand. Tests: a richer cohort hires more
household work; a cohort without a hearth buys cooked food.

Religion as a need is out of scope by owner decision; it is a mod (`mods/TASKS.md`).

## Done

- `data/world/household_work.json`: hours a person's share of household work takes, by task. Water, fuel and grinding
  come from Blackden and Wodon (eds), Gender, Time Use, and Poverty in Sub-Saharan Africa, World Bank Working Paper 73,
  2006, overview p. 9 (opened): an average adult female spends from just under 1 hour to 2 hours 20 minutes a day
  carrying water, firewood and crops for grinding. Cooking, cleaning and childcare hours: no source found, labelled
  estimates (confidence D) with a `retire`.
- `household_work` need in `data/world/needs.json`, no floor, satiation held equal to that file by a test, met by
  `domestic_service_hour` (`data/production/95_household_services.json`), made by the new `domestic_servant` trade
  (`data/world/trades.json`, group `services_state`). `cooked_meal_kg` is the cooked food a cook or eating house makes.
- `sim/economy/households_work.py`: hours needed, hired hours (a richer cohort hires more), own hours, and the basket
  of a household with no hearth (food only from goods marked `ready_to_eat`). Tests: `sim/tests/test_economy_households_work.py`.

## Done in stage 2

- The typed 0.04 is retired. `households_work.hired_hours` hires all of a cohort's household work when an hour of
  its own labour (the wage it faces, averaged over the hours it would sell, `hour_value`) is worth more than the
  servant's price, otherwise none; cohorts differ in what their hours earn, so the aggregate steps up smoothly. The
  servant's price is the `domestic_servant` wage last year, else the tile's subsistence wage per hour. The need's
  `surplus_budget_share` is 0 (`need_data` now allows a need with no share); hired hours are the cohort's floor of
  the need (`Cohort.hired_work_per_person`, set in `sim/economy/household_work_year.py`).
- Own hours are kept back: `Economy._shortfall_hours` adds each cohort's own household-work hours to its own-plot
  hours, so `withhold_hours` cuts the offers; `_grow_own` does not count them as spare hours for the plot.
- Hearth: a cohort has one when it holds a title or a tenancy on its tile (`has_hearth`). No urban marker exists in the
  economy. `cohort_basket` gives a hearth-less cohort `without_hearth_basket` at the cohort sites (opening bids, goods
  orders, year close, household loans); the work of a landless household leaves out cooking.
- Tests: `sim/tests/test_economy_household_work_year.py`, `sim/tests/test_economy_households_work.py`.

## Still to do

- Cooking needs fuel at a hearth: the household's own fuel use is not yet counted apart from the warmth need.
- Land after the opening settles (473). Re-measure with a whole game: the hours kept back are a large share of the
  offered hours (compare `simulator.py economy-check` hired share and wage over floor before and after).
- An urban marker, when one exists, should also remove the hearth.

## PM note (2026-10-21)

The first stage's hired-hours rule takes a typed budget share (0.04) of the cohort's surplus. That is a spending share
typed into the data, the kind of cultural constant 530's decision ruled out. Replace it with the household's own
choice: it hires an hour of household work when an hour of its own labour is worth more at the market than the
servant's price, up to the work there is, so hiring follows income and the wage with no typed share. Retire the
0.04 when that lands.
