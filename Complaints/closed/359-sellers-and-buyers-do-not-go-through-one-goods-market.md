# Sellers and buyers do not go through one goods market: firms' output never reaches the market book

**Status:** closed - pinned by sim/tests/test_one_goods_market.py and sim/tests/test_market_records_ownership.py

The founder buys and sells through `material_trade_quote`, `material_purchase_cost`, `market_note_purchase` and `market_note_sale`; actors buy through the same purchase cost. But a firm's sales are `concern_takings` times a category factor (`economy_goods.py`, `actors/world.py`) and never call `market_note_sale`, so firm output does not lower a price and does not compete with the founder's sales in the book.

What it would take: a `GoodsMarket` with quote, buy, sell and price that the founder, firms, the state and foreign traders all use; firm output sold through it; a test that the same sale by the founder or a firm moves the price the same way.
