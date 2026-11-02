# Labour supply and hiring have no single owner

**Status:** partly - every employer's hires go through the labour core (`sim/markets/port_staff.py`: a seat's places and an actor's `staff_wanted` become standing bids, and the staff are the people the clearing hired); what is left is below

Found by an outside reviewer reading the repository; checked against the code. An integration risk:
no worker has been shown counted twice.

- The agent economy keeps workers by area, trade and ability in `record.workforce`.
- `sim/labour/labour_market_api.py` quotes from the economy's wage but adds its own hiring-pressure
  record (kept on the household state) and the army's standing draw.
- Recruitment reads town supply estimates (`labour_population.py`), the household's employees and
  actors' staffing.

National workforce, local recruitment, standing employment and annual hours are different facts, and
that is fine. What is missing is one allocation they are all derived from, so that an hour given to
one employer cannot also be given to another (551 is one case: own-plot hours and carriage hours).

## What is left

- `seat.employees` is still written directly by `sim/workforce/` (`staff_year.py`, `applying_hours.py`, `commands_applied.py`); the
  reads go through `sim/labour/staff_book.py` (`Labour.employed`, `employed_by_trade`, `set_employed`, `add_employed`).
  `sim/tests/test_labour_single_owner.py` walls the labour modules' writes.
- The hire check reads `hands_available` (`sim/labour/labour_population.py`): the core's people of the trade in the
  tiles reached, or last year's idle hours of it nationwide where those are more; `NO_DEMAND_TRADE_SHARE` stands in for a
  trade the core holds nobody of (`retire` names Complaint 964; `python3 sim/constants.py --burndown` lists it). The idle
  hours are not by tile, so a hire can count hands that are idle elsewhere.
- A seeded trade nobody bids for is bounded to nothing at each trim (`trade_seed.bound_by_hirers`), but the opening's own seed is
  not bounded by the carriage crews it will hire (`trade_seed.seed_hours`).
- Run a real Rome game and read the headcounts the seeding gave (carter, porter, sailor, merchant); the merchant count in the core
  and the population report's `estimated_in_the_country` were measured to disagree (tens against tens of thousands) and have not
  been compared since. Not re-measured on this branch.
- The labour year is described in `sim/labour/market/DESIGN.md`.
