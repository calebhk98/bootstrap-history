# The trader scan grows with places squared, and the concern caches with operators

**Status:** open

Split from 406.

**The trader scan.** Each trader, and the trader entry spawner, prices every (material, source,
destination) triple every year (`Trader.route_options`, `trader_entry.candidate_routes`). With only the
home society and its enabled partners that is small. A scenario with many countries makes it grow with
traders times materials times places squared. Route terms are the same for every trader in a year, so
they could be worked out once per year in the world's memo and read by each trader.

**Concern caches.** `ActorRegistry.capacity_in` and `concerns_in` rebuild from every operator
whenever any operator's concerns change. Many AI players changing concerns each year make that
quadratic in operators. `_ConcernWatch` could keep the totals current incrementally.

There is no measurement command yet: profile `advance_actors` on a scenario with many countries.
