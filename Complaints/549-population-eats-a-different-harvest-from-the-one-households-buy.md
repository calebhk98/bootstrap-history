# Population eats a different harvest from the one households buy and grow

**Status:** partly done. Demography is fed what households ate (national); the farm model still runs for labour, land and the state. Per-tile hunger waits on 603.

Found by an outside reviewer reading the repository; checked against the code.

- Demography's nutrition comes from the engine's farm path in `sim/engine/core.py`: farm workforce,
  harvest, granary, calories, then `Population.step` (`sim/world/demography.py`).
- The agent economy separately makes food, stores and moves it, and decides what each household cohort
  buys and grows (`sim/economy/`, `households_own.py`, `year_goods.py`).
- Nothing feeds demography from what households actually ate, by tile and cohort. A famine in the market
  (a blocked route, a poor cohort priced out) need not starve anyone, and a demographic famine need not
  show in the market.

## What it would take

- One account of food: production (the farm model computing yields, 537), storage, transfers and
  consumption all in the agent economy's book.
- Demography fed from consumption by tile and cohort, so hunger falls where it happens.
- A test: removing a tile's food imports lowers that tile's nutrition and raises its mortality, with
  other tiles unchanged.
- Related: 489 (population national), 507 (prices and volumes have two owners), 513, 537.

## What was done

- `sim/engine/food_eaten.py`: when the economy's year closes (`_step_market`), the nation's people-weighted food
  eaten over need (from `YearAccounts.cohorts`) is kept in `state.population.food_eaten_over_need` (saved). The next
  year's `_demographic_recovery` turns it into the calories a day `Population.step` and `disease_year` are fed.
- Where the old path still feeds demography: a game whose economy has not closed a year (the first year after
  opening, or an economy that never runs). The farm model (workforce, harvest, granary) still runs every year
  because the labour split, land clearing, the state's grain revenue and the granary exposure read it; it no
  longer sets nutrition once a figure exists. Deleting it needs the farm model's outputs in the economy's book (537)
  and the labour split off it.
- Population is one national record, so the hunger is national. Tests: `sim/tests/test_demography_eats_households_food.py`
  (a tile's food cut lowers its figure and the nation's and no other tile's; a national shortfall raises deaths).
  Per-tile mortality needs population by tile (603).
- Measured: `python3 -W ignore` probe of rome_100ad over 5 years: households ate about 1.06 to 1.09 of need, so the
  nutrition ratio demography sees is above one (the farm path capped it at one) and the baseline grows faster. The
  economy rebalances toward need in the engine-free fixture (it did not go hungry when land or harvest was cut), so a
  famine from the market has yet to be exercised end to end.
