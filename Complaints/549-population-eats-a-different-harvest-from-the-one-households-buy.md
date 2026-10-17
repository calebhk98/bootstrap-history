# Population eats a different harvest from the one households buy and grow

**Status:** open

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
