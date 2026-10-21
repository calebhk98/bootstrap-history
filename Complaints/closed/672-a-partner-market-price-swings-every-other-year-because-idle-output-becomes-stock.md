# A partner market's price swings every other year because idle output becomes stock

**Status:** fixed (idle capacity is no longer stock; stock is held at a reservation from its carrying cost)

Under a steady foreign cargo the partner book's price alternates every year: at the producers' floor one year, well below it
the next, then back. Repro: the slow check "...and no longer swings from year to year" in
`sim/tests/test_foreign_actor_trade_scenario.py` (`python3 -m sim.tests --slow --only foreign_actor_trade_scenario --jobs 1`).

**Cause.** At the floor, `sim/world/market.py` `clear_market` counts the society's idle output as `unsold`, and
`stock_after_year` carries it into next year as stock (read by `sim/engine/foreign_actor_trade.py`). Next year that stock is
offered down to `STOCK_FLOOR_RATIO` of cost, below every producer's cost, so the price falls and the stock empties; the year
after, nothing is carried and the price returns to the floor. The two-year cycle comes from the clearing rule, not from the
cargo.

**How it should work.** A producer that cannot sell at its cost does not make the output: it cuts its runs, so idle capacity is
idle, not stock. Stock that does exist (made before demand fell, or a harvest) is held while holding it costs less than what it
is expected to fetch later, and is sold at a reservation price that reads the cost of carrying it (storage, spoilage, interest),
not dumped at a fixed small share of cost. This is the agent economy's rule (`sim/economy/` sellers' reservation search and the
stock gate) and the design the opening work (473) is moving toward; the world-market model here should follow the same rule or
read it.

**What it would take.** `clear_market` stops counting unrun capacity as unsold output; carried stock gets a reservation price from
carrying cost (retiring `STOCK_FLOOR_RATIO`, a labelled heuristic); a rule test on built inputs shows a steady demand gives a
steady price, and the slow check turns green without a change to its bound.

## Done

- `sim/world/market.py`: `clear_market` returns `held_over_tonnes` (goods that exist and did not sell: stock held back or
  unsold, and outsiders' goods the market did not take); `stock_after_year` carries that, less spoilage. Unrun society
  capacity is idle, not stock (`unsold_tonnes` still reports it).
- `stock_reservation_ratio`: the producers' floor less a year's carrying (spoilage `STOCK_RETENTION` and
  `CARRYING_RATE_PER_YEAR`, a labelled heuristic). Stock and price takers sell down to it and hold below it.
  `STOCK_FLOOR_RATIO` is deleted.
- Tests: `sim/tests/test_market_clearing.py` (`StockIsHeldAtItsCarryingCostTests`: a steady demand gives a steady price;
  a one-off surplus is sold down over years above its reservation; stock is held rather than sold below it).
  The slow check "...and no longer swings from year to year" passes with its bound unchanged.
- Two neighbouring checks in `test_foreign_actor_trade_scenario.py` relied on the phantom stock to push the partner's
  price down under a cargo smaller than the partner's demand. They now say what the market does: the cargo displaces the
  partner's producers, who idle, and the price stays at their floor (it gives way only once the cargo outgrows demand).
  Whether competing carriers should bid that price down is a trader question, not the clearing's.
