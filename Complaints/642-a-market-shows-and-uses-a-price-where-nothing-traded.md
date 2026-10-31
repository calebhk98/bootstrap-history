# A market shows and uses a price where nothing traded

**Status:** partly fixed (clearing, memory, the price index, the cap, the opening estimate's kind, the player's screen and what buyers read; the items under Left remain)

`goods_market` (`sim/economy/goods_market.py`, the clearing that returns `held_price`) returns the last price when a
market has no offers, when what is offered is residue, or when no buyer wants anything; `market_memory.py` keeps a
remembered price after the cleared one is dropped, and PR #60 capped such remembered prices at a multiple of making cost
(`f3a2db9b`, a labelled heuristic). These prices are shown to the player and read by producers, merchants and the price
index (558: `economy_state_budget`'s index follows thin goods).

A price no one traded at is not a price both parties agreed to. It is the source of the extremes in thin markets that
the cap only clamps.

What it would take: a market's price exists only for a year it traded. Otherwise the market reports its bid and ask
(the best unfilled bid, the lowest unfilled ask, or a cost-covering quote from a producer able to make the good), each
named as what it is. Every reader of the price says which it needs, and the cap goes. Tests call the clearing with built
books: no trade gives no price and a quote; a trade gives its price.

## Done

- `goods_market.clear` returns `ClearingResult.traded_price` (None when nothing traded) and `ClearingResult.quote`
  (`types.Quote`, kind `best_unfilled_bid`, `lowest_unfilled_ask` or `cost_covering`; built by `market_quote.py`).
  The `price` field of a no-trade result is the solver's working crossing, not a price anyone traded at.
- `year_goods`: a market that traded updates its remembered price from the trade (as before); a market that did not
  moves its planning price part of the way to its quote (`market_memory_offers.price_toward_quote`, share
  `NO_OFFER_MEMORY_SHARE`, now `retire`d to this complaint) and records the quote's kind in
  `MarketMemory.quote_kinds`. Taken whole, a cost-covering quote told every maker its runs pay and no mine left
  (`economy_exit`), so the planning memory is smoothed and the kind says what it follows.
- Removed: `PRICE_OVER_MAKING_COST_LIMIT` and `price_within_making_cost`, `price_after_no_bids`, `price_after_no_offers`,
  `NO_BID_MEMORY_SHARE`, `year_goods._unsold_signal` (the best-unfilled-bid quote replaces it).
- Readers, by which they read:
  - traded only: `MarketView.cleared_price` (producers.paid_input_prices), `MarketMemory.cleared_prices`,
    `national_prices` (the price index: areas that traded, the quote figure only for a good no area traded; 558);
  - planning price, traded or quote, with `MarketView.quote_kind` saying which: `MarketView.price` and
    `prices_across` / `price_rows` (households, producers, entry, merchants), `learned_prices` (traders);
  - display: `notional.py` still estimates goods that have not traded lately; interface and engine readers of
    `memory.prices` (`engine/commodities.py`, `engine/economy_port_actors.py`) have not been moved to
    `quote_kind`.
- Tests: `test_economy_no_trade_no_price.py` (built books: a trade gives its price and no quote; no trade gives no
  price and a named quote; the index follows traded areas; the view names a quote), `test_economy_frozen_markets.py`,
  `test_economy_year_goods.py`, `test_economy_no_offer_memory.py`. `test_economy_price_within_making_cost.py` deleted.

- The opening estimate has a kind: `MarketMemory.price_kind` (and `MarketView.price_kind`) name a remembered price as
  `traded`, its quote kind, or `QUOTE_OPENING_ESTIMATE`; `notional.shown_prices_with_kinds` adds the estimate kinds
  (`making_cost_estimate`, `thin_trade_blend`, `remembered_price`); `api.shown_price_kinds_of` and
  `EconomyPort.agent_price_kind` carry it to the engine.
- Readers moved: `GoodsMarket.quote` carries `price_kind` (`goods_market_pricing.price_kind`: the economy's kind,
  `making_cost_table` where the economy has no market, `partner_landed_price`); the `market` screen row shows "no trade:
  <cause>" for any price that is not a trade (`render_screens_market.price_note`); the founder's standing bid takes no price
  where there is none (`economy_port_actors.standing_price`) and the seat sales weights no longer read a missing price
  as 0.0 (`economy_port_seats.record_year`). `engine/commodities.py` reads no market price (no read of
  `memory.prices` or `MarketView` in it).
- Tests: `test_economy_price_kinds.py`, `test_goods_market_pays_economy_price.py` (the quote's kind).

- Buyers read what is offered, not a remembered price (follows Eurace's consumers, who see only the mall's current
  prices: `Cons_Goods/Household_Consumer_Functions.c`). `MarketMemory.offered_price` / `YearView.offered_price` /
  `offered_price.offered_price(view, good, area)` give the traded price, an ask still posted (`lowest_unfilled_ask`) or the
  opening's estimate before any clearing, and None for a bid ceiling, a cost quote or a price remembered from an old trade.
  A price from an old trade that nothing replaced now has its own kind, `PRICE_REMEMBERED` (it was reported as the
  opening estimate). Moved to it: `households_basket.need_prices` (:37), `households_store` (`price_rows` and the
  fallback read), the tool bids (`year_goods.py` :55) and the work-need price (`household_work_year.py` :76).
- Readers kept on the planning price, with the reason: producers' output expectations (`producers.py` :114, :227) read the
  price with the quote kind (`planning_price.is_bare_quote` holds a bare quote to the cost band) because a seller's own
  last price is its expectation; producers' input costs (`producers.py` :156, :237, `producers_close.py` :126) are
  estimates, and an input with no price would make a run cost infinity and stop every maker that uses it; the valuations
  (`producers_close.inventory_value`, `capital_year.py` :126, `land_bid_year.py`, `entry_trial.py`, `entry_margin.py`,
  `economy.py` :462) are estimates of worth, not purchases.

## Left

- A no-trade market with nothing to quote keeps its old remembered price in the planning memory (buyers no longer read
  it; its kind is now `remembered_price`).
- The thin-trade relaxation (`price_after_thin_trade`) still moves a traded price toward cost in the planning memory; the
  display labels the blended figure `thin_trade_blend`. Producers still plan from the memory.
- Not moved, owned by the parallel work: `merchants.py` (:128, :224, `prices_across`; a merchant buying at a source
  should read the offered price), `opening.py` (:143, :215 `view.price(...) or 0.0`), `carriage_fleet_book.py` :163.
- In-band zeros that remain: `land_bid_year.py` :23, `entry_margin.py` :79, `economy.py` :462 read a missing price as 0.0.
