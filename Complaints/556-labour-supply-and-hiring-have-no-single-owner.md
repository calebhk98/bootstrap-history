# Labour supply and hiring have no single owner

**Status:** open

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
