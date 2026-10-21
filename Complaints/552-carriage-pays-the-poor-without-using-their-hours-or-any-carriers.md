# Carriage pays the poor without using their hours or any carriers

**Status:** partly - hours, fleets, wear, storage and fee split are built (627 to 632, all closed); open: carrier trades are not answering the bids in a real game (crew is bid as unskilled labour)

Found by an outside reviewer reading the repository; checked against the code. Full history of the split: `Complaints/reports/552-history.md`.

## What is wrong now

- The crew hours a merchant bids are placed in the unskilled trade, not the carter or sailor trade of the mode
  (`CARRIAGE_CREW_UNSKILLED_SHARE`, a labelled temporary heuristic, retire 556). Reason: the opening places people by the runs
  producers expect, so no carters exist when merchants first ship, and the labour core does not grow a new trade fast enough.
  Lowering the share makes the code bid each mode's own trade. Find it: `grep -rn CARRIAGE_CREW_UNSKILLED_SHARE sim`.
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

- Seed the labour core with the trades the flows need (556), then lower `CARRIAGE_CREW_UNSKILLED_SHARE` to zero and delete it.
- One real-game trace (for example `python3 sim/simulator.py economy-check --accounts --years N --civs rome_100ad`) showing carter, sailor and porter hours demanded and hired, and that shortcut unused.

## Tried

- Bidding each mode's own trade from year one: no carriers exist then, so hours went undelivered; hence the unskilled share.
