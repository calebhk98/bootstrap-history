# Labour supply and hiring have no single owner

**Status:** partly done. The founder's staff book has one owner (`sim/labour/staff_book.py`); the core is seeded with every trade the society's need names (`labour_state.seeded_hours`, `sim/labour/trade_seed.py`); hires are viewed out of the core's people by tile and trade (`core_reservations.py`); open: the real-game check and the two share heuristics (below).

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

Done (behaviour change; the figures below are one measurement on an opened Rome game, re-measure with this command: `python3 -m sim.tests --slow --only labour_single_owner`):

- Cause of the split: the opening placed only the people producers' expected sales need and sent everyone else to
  the unskilled trade, and the post-spin-up trim sent every cut worker there too. Farm people mostly work their
  own plots (`households_own.py`), so no producer hires them and the core held them as `labourer` while the
  estimate booked them as `farmer`. Now people no employer needs work as the plot trade (`labour_state.plot_trade`,
  the trade the land-only recipes ask most hours of) in `opening_state(idle_trade=...)` and
  `workforce_settle.send_idle_to_plots`.
- `national_trade_population` returns the core's headcount for any trade the core holds people in; the
  literacy-counted trades (scholar, scribe, merchant), the draft pool (soldier) and founder-taught trades are
  counts the core does not hold and keep their estimates, and a trade the core holds nobody in keeps the old
  estimate until the core seeds it ([temporary_heuristic] shares in `labour_population`; they retire when this complaint seeds the core, see Remaining).
- Measured on an opened Rome game (people, core and estimate now equal): farmer 26.6M -> 28.5M (core was 39.7k),
  labourer 181k -> 1.19M (core was 29.6M), smith 79.7k -> 1.2k, mason 38.6k -> 305k, weaver 70.3k -> 33.2k.
  Hiring caps (`market_supply`) are unchanged: the town cap binds, not the national count.

Done (seeding and reservations; rule tests in `test_labour_core_seed_and_reservations.py` and `test_labour_population_unskilled_family_share.py`):

- A trade the society's recipes and carriage need but no producer's runs staff (carter, porter, sailor, artisan, ...) is seeded in the opening
  with hours in the ratio of its need share to the staffed trades' (`trade_seed.seed_hours`); the post-spin-up trim keeps those hours. The
  need shares ride in the opening values (`need_shares`, `EconomySetup.need_share_by_trade`).
- Before the core opens, a labour-family trade's national estimate is its own share of work (porters and carters differ), not one town share.
- The founder's hires are taken out of the core's people at the base tile by trade (`Labour.free_core_people_by_tile`, `reservations_over_core`);
  `core_reservations.reserved_hours_within_people` is the hours-reserved boundary.
- Carriage crews are bid in each mode's own trade; `CARRIAGE_CREW_UNSKILLED_SHARE` is deleted (552).

## Remaining

- Run a real Rome game and read the headcounts the seeding gave (carter, porter, sailor); the seeds keep their people only while an employer bids for them, and the core's yearly clearing moves unemployed people away (re-measure before closing).
- Move the plague survival roll (`sim/engine/society_hazards.py`) and the `core.py` / `economy.py` dict wrapper under the owner.
- `UNSKILLED_POOL_TOWN_SHARE` (the town's hiring cap for the farm, army and fallback trades) and `NO_DEMAND_TRADE_SHARE` (rank trades and the estimate before the core opens) stay, each with `retire` naming this complaint, until the town cap reads the core's people by tile.

## The opening seeds a glut in trades no producer staffs (PM, measured 2026-10-22)

`complaint_467_trades_open_to_the_jobs` is red: the opening seeds glassblowers, knappers, plumbers and merchants by need share
(`labour_state.seeded_hours`), for example about eighteen thousand merchants against about a hundred and fifty worker-years of
producer bids, so they wait for carriage crews and recipes no producer runs. A seed by need share should be bounded by the work
the opening's producers, carriers and state will hire. The test that held this command was removed from the suite.

Done: the trim after the spin-up keeps a seeded trade only as far as its hirers' hours go (`workforce_settle.hours_kept`: what
producers plan and others hired last year, plus the state's bids; `trade_seed.bound_by_hirers`); the people beyond that join the
fallback trade. A trade whose hirers bid more than the seed is unchanged. The opening's own seed is still by need share (the
spin-up's carriage bids need those people); the bound applies at each trim. Rule tests: `SeedBoundedByHirersTests` in
`test_labour_core_seed_and_reservations.py`. `complaint_467_trades_open_to_the_jobs` is green. Merchants, glassblowers, knappers and plumbers
after the open: see the commit message. Still open: the opening seed itself is not bounded by the carriage crews it will hire.

Done (carters, 2026-10-22): `carters_and_plumbers_exist_in_a_game_scenario` went red because the bound read no hirer for the carriage
trades: at the trim the producers' plans and last year's hires (`expected_hours`) hold none of them (the carriage crews' hours are in
neither), and the state does not bid them, so every carter seed went to the fallback. The merchants' planned carriage hours
(`carriage_hours.bids`, summed by `workforce_settle.carriage_plan_hours`) are now a hirer in `hours_kept`, as producers' plans are. A seeded
trade nobody plans for or hires is still bounded to nothing. Rule tests: `SeedBoundedByHirersTests`. Re-measure the counts with
(the test was removed from the suite).

## Two readers disagree on the merchant count (PM, 2026-10-22)

After the seed bound, the labour core's opening count of merchants in Rome was measured in the tens, while the population
report's `estimated_in_the_country` gives tens of thousands. Either the report reads a different stock (the merchant stratum,
not the trade's workforce) or the two readings disagree; check which before trusting either figure.
