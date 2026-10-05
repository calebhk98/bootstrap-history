# The trader scan grows with places squared, and the concern caches with operators

**Status:** partly - the route scan prunes by price gap (sim/tests/test_trader_route_scan.py); the concern caches still rebuild from every operator

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

## What landed

`sim/agents/trader_routes.py` finds a material's gaining pairs by a sorted search on price (a pair can only gain if the destination price exceeds the source price by the share lost on the way), and prices carriage for those pairs alone. `Trader.route_options` and `trader_entry.candidate_routes` both use it and return what the exhaustive scan returned (tests compare against it on random worlds, in order). Carriage pricing no longer grows with places squared; the sort and the price reads still grow with places.

Not done: the concern caches. `capacity_in` and `concerns_in` depend on both concern sets and each firm's capacity, which changes through `note_capacity_change` without a concern change, so incremental totals need per-firm capacity deltas, not just `_ConcernWatch`. Cross-trader sharing of route terms was not needed once the scan is pruned.
