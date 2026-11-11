# Carriage pays the poor without using their hours or any carriers

**Status:** partly - hours, fleets, wear, storage and fee split are built (627 to 632, all closed); crew is bid in each mode's own trade and the labour core is seeded with the carrier trades (556); open: run the carriage report on Rome and Mexica (the report is built, not yet run)

Found by an outside reviewer reading the repository; checked against the code. Full history of the split: `Complaints/reports/552-history.md`.

## What is wrong now

- The crew hours a merchant bids are placed in the mode's own trade (`carriage_hours.crew_trades`); `CARRIAGE_CREW_UNSKILLED_SHARE` is deleted.
  The opening seeds the labour core with carters, porters and sailors from the society's need (556, `seeded_hours` in `sim/economy/labour_state.py`). Unverified in a
  real game: whether those people stay in their trades through the first years or the bids go unanswered.
- On a real opening only carts and pack animals are supplied in the first years: no shipwright or saddler trade exists to answer
  the bids for ships and saddles (533, 530 own the missing trades).
- No trace on a real game (not the fixture) shows carrier trades answering the bids; the tests are rule tests and fixtures.

## What is built (where to look)

- Hours hired in the labour market before goods move: `sim/economy/carriage_hours.py` (627); route-following crew and handling hours; area wages through `CarriageTable.set_scale`. Tests: `sim/tests/test_economy_carriage_hours.py`, `test_carriage_hours_by_route.py`.
- Carriers as goods with sourced service lives (629): `data/production/99_carriers.json`, `data/world/service_lives.json`, `sim/economy/carriage_wear.py`. Fleets limit dispatch (631): `carriage_fleet.py`, `carriage_fleet_book.py`, `sim/tests/test_merchant_fleet.py`. The non-labour part of a fee is paid by supplier (632).
- Travel time, spoilage and interest on a haul: `sim/economy/merchants_transit.py`, `sim/tests/test_merchant_travel_time.py`; storage at stages (628).
- Working-capital loans for carrier wages (`carriage_hours.wage_loans`) so a merchant without cash can pay hired hours.
- Remaining shortcut: where the setup names no carriers, the whole fee still goes to the poorest household of the source tile (docstring of `dispatch_merchants`, `sim/economy/year_close.py`).

## What it would take

- The report exists: `python3 sim/simulator.py economy-check --accounts --carriage --years 5 --civs rome_100ad` (and `--civs mexica_1500`) prints, per year, the crew hours merchants bid and the hours the labour market sold them per carrier trade, and the carriage fee paid to a household of the source tile (the shortcut) against the edge account (`sim/economy/carriage_report.py`, test `sim/tests/test_carriage_report.py`). Close when carter, sailor (Rome) and porter (Mexica) rows show hired hours near the demanded ones and the fee to households is zero or small against the hired wages.
- The shortcut is not dead code: `dispatch_merchants` still pays the fees it computes (crew pay owed for hours not hired, notably a merchant's first year with no plan) to `poorest_by_tile`, so it cannot be deleted before the report shows how much it pays.

## Tried

- Bidding each mode's own trade from year one: no carriers exist then, so hours went undelivered; hence the unskilled share.
