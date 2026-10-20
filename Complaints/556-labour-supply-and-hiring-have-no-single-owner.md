# Labour supply and hiring have no single owner

**Status:** partly done. The founder's staff book has one owner (`sim/labour/staff_book.py`); the supply estimate is still a second copy of the core's people (below).

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

## What it would take

- One workforce owner (the labour core, `sim/labour/market/`) that every employer, founder, firm, state
  and household plot, reserves hours through; local and national figures as views of it.
- A boundary test: total hours reserved in a year never exceed the hours the population supplies, by
  tile and trade.
- Related: 428 (closed, the core sets wages), 508.

## Progress

Measured on an opened Rome game (`python3 -m sim.tests --slow --only labour_single_owner`):

- The labour core's people by trade and the town-supply estimate (`national_trade_population`) are two
  copies that disagree: the core holds the unskilled pool as nearly all working people while the estimate
  gives it a small town share; the farmer and smith counts differ the other way. The test asserts the gap.
- A hire writes the founder's book and is invisible to the core's people: reservations are never taken out
  of the core, so the core cannot enforce that hours are not given twice.
- No trade was found with reservations over the supply the hire path already caps at.

Done (behaviour preserving, quick tier and the labour, staffing, firm and save topics green):

- `sim/labour/staff_book.py` (`Labour.employed`, `employed_by_trade`, `employed_total`, `set_employed`,
  `add_employed`, plus the views `reserved_people`, `reserved_hours`, `supplied_people`, `unreserved_people`,
  `core_people_by_trade`) owns the founder's staff. Every labour module and the engine's staffing phases
  read and write through it; `sim/tests/test_labour_single_owner.py` walls the writes.
- Still outside the owner: the plague survival roll in `sim/engine/society_hazards.py` (listed as a test
  exception until the disease work lands), and the dict wrapper in `core.py` / `economy.py`.

Remaining: make `national_trade_population` and the hiring cap a view of the core's people (a behaviour
change, needs before and after values), and take hires out of the core's people by tile and trade.
