# A market shows and uses a price where nothing traded

**Status:** partly fixed (clearing, memory, the price index and the cap; display readers and the opening estimate still to move)

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

## Left

- Opening estimates (`opening.py`, `late_recipes.py`) are still stored in `memory.prices` with no kind.
- A no-trade market with nothing to quote keeps its old remembered price.
- `engine/` readers and the player display should show `quote_kind`.
- The thin-trade relaxation (`price_after_thin_trade`) still moves a traded price toward cost.
