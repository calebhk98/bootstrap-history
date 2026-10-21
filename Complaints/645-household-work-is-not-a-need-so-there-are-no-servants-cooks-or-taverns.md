# Household work is not a need, so there are no servants, cooks or taverns

**Status:** partly done: data, trade, recipes and the pure rules are in; the engine does not yet keep own hours back or give a hearth-less cohort its own basket

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

## Still to do

- Keep a cohort's own household-work hours back from its labour offers (`withhold_hours`), from last year's hired hours.
- Decide which cohorts have a hearth (551: no land or tenancy; urban) and give them `without_hearth_basket` at the
  `setup.basket_for(cohort.tile)` sites.
- Cooking needs fuel at a hearth: the household's own fuel use is not yet counted apart from the warmth need.
- Land after the opening settles (473).
