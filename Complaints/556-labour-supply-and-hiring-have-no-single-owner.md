# Labour supply and hiring have no single owner

**Status:** partly - every employer's hires go through the labour core (`sim/markets/port_staff.py`: a seat's places and an actor's `staff_wanted` become standing bids, and the staff are the people the clearing hired); what is left is below

Found by an outside reviewer reading the repository; checked against the code. An integration risk:
no worker has been shown counted twice.

- The agent economy keeps workers by area, trade and ability in `record.workforce`.
- `sim/labour/labour_market_api.py` quotes the economy's wage and hires through the labour core (the hiring-pressure
  record and the army's own draw this item once described are deleted; the state's call-up of hours for works and army is `sim/markets/port_levy.py`).
- Recruitment reads town supply estimates (`sim/labour/labour_supply.py`), the household's employees and
  actors' staffing.

National workforce, local recruitment, standing employment and annual hours are different facts, and
that is fine. What is missing is one allocation they are all derived from, so that an hour given to
one employer cannot also be given to another (551 is one case: own-plot hours and carriage hours).

## What is left

- Done: `seat.employees` is written only through `sim/labour/staff_book.py` (`set_employed`, `add_employed`, and `record_hired` for
  the clearing's `StaffArrived`); `sim/workforce/` only reads it (apart from `staff_watch.py` wrapping the dict to report changes).
  `sim/tests/test_labour_single_owner.py` covers the book's writes.
- The hire check reads `hands_available` (`sim/labour/labour_supply.py`; `hands_available` in `sim/labour/hands.py` is a different rule: staff, the founder and contracted hours): the core's people of the trade in the
  tiles reached, or last year's idle hours of it nationwide where those are more; `NO_DEMAND_TRADE_SHARE` stands in for a
  trade the core holds nobody of (`retire` names Complaint 964; `python3 sim/constants.py --burndown` lists it). The idle
  hours are not by tile, so a hire can count hands that are idle elsewhere.
- A seeded trade nobody bids for is bounded to nothing at each trim (`trade_seed.bound_by_hirers`), but the opening's own seed is
  not bounded by the carriage crews it will hire (`trade_seed.seed_hours`).
- Run a real Rome game and read the headcounts the seeding gave (carter, porter, sailor, merchant); the merchant count in the core
  and the population report's `estimated_in_the_country` were measured to disagree (tens against tens of thousands) and have not
  been compared since. Not re-measured on this branch. Command: `python3 sim/simulator.py economy-check --occupations --years 3 --civs rome_100ad`.
- The labour year is described in `sim/labour/market/DESIGN.md`.
