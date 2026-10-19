# Sell reports stock left that the next sell does not find

**Status:** closed - `sell` reads one holding and refuses a sale of more than is held with `not_enough_held`

Found by an agent playtest (`Complaints/reports/playtest-rome-seed11-agent-legitimate-log.md`, 111 to 125 AD). A `sell` reply said over a thousand tonnes were left; the next
`sell` found a small fraction of that. A `sell` of more than is held errors out instead of refusing with a `cause`.

What it would take: the reply's stock left reads the same holding the next sale draws on (one function), and selling
more than is held is a refusal with `cause: "not_enough_held"` and the quantity held; tests for both.

## Resolution

The next sale was cut by what the market still absorbs this year, a figure the reply never showed. `sell` now reads
`GoodsMarket.sale_limits` (held tonnes, market room) before and after, refuses more than is held with cause
`not_enough_held` and the held tonnes, refuses a full market with `market_full`, and the reply carries
`stock_on_hand_tonnes` and `market_will_still_take_tonnes` from the same function the sale uses.
Test: `sim/tests/test_complaint_578_sell_stock_left.py`.
