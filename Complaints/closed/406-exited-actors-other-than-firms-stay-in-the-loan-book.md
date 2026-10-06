# Exited actors other than firms stay in the loan book

**Status:** closed - the loan book drops any exited actor; pinned by sim/tests/test_capital_market.py (the exited trader check)

**The loan book.** `market_loans` (`sim/engine/economy_capital_market.py`) leaves out an exited
actor only when its kind is `"firm"`. Traders now exit too (`sim/agents/trader.py`), and so may any
mod's kind. An exited trader's debt stays among "what others owe" for good, because its interest stops
with its turns. That shrinks every borrower's credit headroom. The actors' own registry skips any
exited actor (`ActorRegistry.advance`). The loan book should test `record.exited_year` whatever the
kind, so the engine no longer names a kind.

The trader scan and the concern caches moved to 462.
