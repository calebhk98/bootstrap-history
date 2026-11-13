# Labour supply and hiring have no single owner

**Status:** closed - every employer hires through the labour core, one owner writes the staff, the hire check and the opening seed are bounded by tile and by carriage hours; the Rome headcount read is a check in the notes

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
- Done: the hire check reads the core's people of the trade in the base tile's labour area (`Supply.hands_available`, `_people_of_trade_in_reach`);
  other tiles' people and idle hours are not counted (`sim/tests/test_labour_single_owner.py`). `NO_DEMAND_TRADE_SHARE` stands in only where the
  core holds nobody of a trade there (`retire` names Complaint 964; `python3 sim/constants.py --burndown` lists it).
- Done: the opening's seed of a carriage-only trade is cut to the crew hours the merchants' carriage will ask there (`sim/economy/carriage_opening_hours.py`:
  each merchant carries its capital's worth of tonnes the average haul to the populous tiles, as its opening fleet is sized; `opening_placement.seeds_where_hired`).
  Each later trim bounds it by the real bids (`workforce_settle.hours_kept`).
- Explained: the population report's `estimated_in_the_country` and the occupation tables both read the labour core's people by trade
  (`economy.agent_people_by_trade`); the old tens against tens of thousands came from an estimate that no longer exists. They differ only for the
  soldier (working age), a trade only the founder teaches, and a trade the society lacks.
- A check, not a defect: read a real Rome game's headcounts for carter, porter, sailor and merchant once:
  `python3 sim/simulator.py economy-check --occupations --years 3 --civs rome_100ad`.
- The labour year is described in `sim/labour/market/DESIGN.md`.
