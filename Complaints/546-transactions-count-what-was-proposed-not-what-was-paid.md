# Transactions count what was proposed, not what was paid

**Status:** open - all three defects fixed and tested; producers now ask for working-capital loans; `economy_vessel_price_fixture` (dug input price swing) still fails

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

- At a year's close a producer whose cash cannot pay the smoothed runs next year's plan will try asks for a
  one-year loan (purpose `working capital`, no plant) at up to the yearly return of those runs. It takes the
  producer's single loan slot only when it asks no expansion loan.
- `economy_vessel_price_fixture` still fails: the fixture's dug clay price crashes in one year and recovers
  (`python3 -m sim.tests --only economy_vessel_price_fixture`). The diggers' cash is not what limits them
  there; their runs swing between idle and busy with the price they expect.
- Re-measure the spin-up (473); it is a long command and has not been run.
