# A market shows and uses a price where nothing traded

**Status:** open

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
