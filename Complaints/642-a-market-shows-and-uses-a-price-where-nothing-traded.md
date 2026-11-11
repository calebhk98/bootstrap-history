# A market shows and uses a price where nothing traded

**Status:** partly fixed (clearing, memory, the price index, the cap, the opening estimate's kind, the player's screen, what buyers and merchants read at a source; two planning-memory items under Left wait on an owner decision about what producers plan from)

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
    `memory.prices` (`engine/commodities.py`, `engine/port_actors.py`) have not been moved to
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
  where there is none (`port_actors.standing_price`) and the seat sales weights no longer read a missing price
  as 0.0 (`port_seats.record_year`). `engine/commodities.py` reads no market price (no read of
  `memory.prices` or `MarketView` in it).
- Tests: `test_economy_price_kinds.py`, `test_goods_market_pays_economy_price.py` (the quote's kind).

- Buyers read what is offered, not a remembered price (follows Eurace's consumers, who see only the mall's current
  prices: `Cons_Goods/Household_Consumer_Functions.c`). `MarketMemory.offered_price` / `YearView.offered_price` /
  the reader in `sim/economy/producers.py` (`view.offered_price`; the module `sim/economy/offered_price.py` is gone) give the traded price, an ask still posted (`lowest_unfilled_ask`) or the
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

Owner design decisions (what a producer plans from when a market did not trade; not guessed here):

- A no-trade market with nothing to quote keeps its old remembered price in the planning memory (buyers no longer read
  it; its kind is `remembered_price`). Dropping it leaves producers' output expectations and input cost estimates with no
  price, which would stop every maker that uses the good; the substitute (the cost band, the last trade aged, or a
  refusal that makes the maker idle) is not chosen.
- The thin-trade relaxation (`price_after_thin_trade`) moves a traded price toward cost in the planning memory; the
  display labels the blended figure `thin_trade_blend`. Whether producers plan from the traded price alone (as
  `cleared_price`) or from the blend is not chosen.

## Also done (merchants, and the stale line items)

- A merchant buying at a source reads what is on offer: a full route search leaves out a source where the merchant has no
  expectation and `offered_price` is None (`merchants_search.unoffered_areas` for `merchants.candidate_routes`;
  `merchants_book.buyable_sources` / `only_sources` for the book and batch searches). The area is still sold into
  (destinations read the planning price). A search for goods the merchant holds is not gated. Test:
  `test_merchant_buys_only_what_is_offered.py`.
- Checked and already done, nothing left: `opening.py` and `carriage_fleet_book.py` have no `or 0.0` on a price (the
  fleet bid reads `offered_price` and skips None); `land_bid_year.best_margin` skips a recipe with an unpriced output and
  `land_bid.hectare_bid` returns no bid for a missing price; `entry_margin` drops a market with no price;
  `economy._bid_for_plant` skips a plant good with no price.
- Still in-band by design: the route search arrays (`RoutePass.view_prices`, `merchants_search.good_routes`) hold 0.0 for
  "no price" inside the compiled kernel, which treats 0 as none; no caller outside it reads that array as a price.
