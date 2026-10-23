# Carriage pays the poor without using their hours or any carriers

**Status:** partly - hours, fleets, wear, storage and fee split are built (627 to 632, all closed); crew is bid in each mode's own trade and the labour core is seeded with the carrier trades (556); open: a real-game trace of carter, porter and sailor hours hired

Found by an outside reviewer reading the repository; checked against the code. Full history of the split: `Complaints/reports/552-history.md`.

## What is wrong now

- The crew hours a merchant bids are placed in the mode's own trade (`carriage_hours.crew_trades`); `CARRIAGE_CREW_UNSKILLED_SHARE` is deleted.
  The opening seeds the labour core with carters, porters and sailors from the society's need (556, `labour_state.seeded_hours`). Unverified in a
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

- One real-game trace (for example `python3 sim/simulator.py economy-check --accounts --years N --civs rome_100ad`) showing carter, sailor and porter hours demanded and hired, and that shortcut unused.

## Tried

- Bidding each mode's own trade from year one: no carriers exist then, so hours went undelivered; hence the unskilled share.
