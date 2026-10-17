# Transactions count what was proposed, not what was paid

**Status:** open - all three defects fixed and tested; the settled-fixture topics `economy_service_lives` and `economy_vessel_price_fixture` fail since the producers fix, awaiting a decision (see below)

Found by an outside reviewer reading the repository; each point checked against the code. Money
conservation holds (the book balances), which is why the suite passes; these are about which
quantities drive decisions.

1. **Smoothing overrides affordability.** `plan` (`sim/economy/producers.py`) limits runs to what the
   producer's cash and stock can pay for, then `within_a_years_change` raises them back to at least last
   year's runs less a year's change. A producer with no cash can plan most of last year's output. Only
   the land cap is applied after smoothing.
2. **Unpaid labour is delivered.** `YearLedger.note_labour` (`sim/economy/year_ledger.py`) counts hours
   in proportion to wages paid only when `settled = bool(postings) and result.wage > 0.0`. A settlement
   that paid nothing has no postings, so every hour counts as hired and sold. The reviewer reproduced
   zero cash, zero payments and the full hours recorded, in isolation and in a Rome run.
3. **Goods volumes are the clearing proposal.** `year_goods` (`sim/economy/year_goods.py`) settles a
   cleared market, records buyers' shortfalls in `ledger.unpaid`, and then stores `result.quantity`, the
   proposed volume, in `record.volumes` and the market memory, which feed expectations and entry.

## What happens now

1. `plan` smooths toward last year's runs first, then limits them to what cash and stock pay for and what
   unsold output allows; only then does the land cap apply.
2. `YearLedger.note_labour` counts hours from the wages actually paid. A settlement that paid nothing
   delivers no hours; a caller with no settlement passes `settled=False` to count the fills in full.
3. `clear_goods` records the volume that changed hands (the goods moves the settlement posted) in
   `record.volumes` and the market memory, and counts a market as traded only when something was delivered.

Regression tests: `sim/tests/test_economy_delivered_not_proposed.py`.

## Open

- With affordability applied after smoothing, the test fixture's smelters run short of cash and their
  output swings for decades (`python3 -m sim.tests --only economy_service_lives,economy_vessel_price_fixture`
  fails three checks that read a settled fixture). Decide whether working capital should come from credit
  or the settled-fixture bounds should move.
- Re-measure the spin-up (473); it is a long command and has not been run.
