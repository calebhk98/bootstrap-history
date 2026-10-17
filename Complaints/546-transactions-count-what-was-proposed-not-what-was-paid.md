# Transactions count what was proposed, not what was paid

**Status:** open

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

## What it would take

- Regression tests first (6, TDD): a cashless producer plans no runs it cannot pay for; a labour
  settlement that pays nothing delivers no hours; a goods settlement with a shortfall records the
  delivered volume.
- Then: apply cash and resource limits after smoothing; count hours from payments made, with an explicit
  flag for callers that pass no settlement; record delivered quantities.
- Re-measure the spin-up (473) after each, since each changes behaviour.
