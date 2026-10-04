# Exited actors other than firms stay in the loan book, and the trader scan grows with places squared

**Status:** open

**The loan book.** `market_loans` (`sim/engine/economy_capital_market.py`) leaves out an exited
actor only when its kind is `"firm"`. Traders now exit too (`sim/agents/trader.py`), and so may any
mod's kind. An exited trader's debt stays among "what others owe" for good, because its interest stops
with its turns. That shrinks every borrower's credit headroom. The actors' own registry skips any
exited actor (`ActorRegistry.advance`). The loan book should test `record.exited_year` whatever the
kind, so the engine no longer names a kind.

**The trader scan.** Each trader, and the trader entry spawner, prices every (material, source,
destination) triple every year (`Trader.route_options`, `trader_entry.candidate_routes`). With only the
home society and its enabled partners that is small. A scenario with many countries makes it grow with
traders times materials times places squared. Route terms are the same for every trader in a year, so
they could be worked out once per year in the world's memo and read by each trader.

**Concern caches.** `ActorRegistry.capacity_in` and `concerns_in` rebuild from every operator
whenever any operator's concerns change. Many AI players changing concerns each year make that
quadratic in operators. `_ConcernWatch` could keep the totals current incrementally.

There is no measurement command yet: profile `advance_actors` on a scenario with many countries.
