# Revenue forecasts and the cash book disagree with takings

**Status:** partly - the forecast now says when it rests on long-run cost (`forecast_basis`) and the cash book matches the itemised revenue; the takings of a good on its first sale (the lottery fetched about ten times its long-run cost) are still not forecast

Found by an agent playtest (`Complaints/reports/playtest-rome-seed11-agent-to-221.md`, from 120 AD). `fin_lottery` was forecast at tens a year and took thousands;
in 139 AD the cash book booked several times the revenue the money breakdown itemised. 577 put quotes and takings
on one function for concerns not yet open; the lottery and the cash book's revenue line still disagree with it.

What it would take: the forecast, the yearly takings and the cash book's revenue line read one function each year
(screens and engine read one number); a test that a running concern's forecast for the year matches its takings
within the year's price change, and that the cash book's revenue equals the itemised revenue.

## Resolution

A concern whose goods nobody had sold had its sales valued at long-run cost but its inputs at live market prices, so the quote was nothing and then jumped once a market existed. `node_output_market_factor` now values the whole net at long-run cost while the economy has no price for the concern output (`concern_goods_have_market`), and `venture_forecast_basis` (`market` or `long_run_no_market_yet`) is carried as `forecast_basis` on `why` and `ventures`. For a running concern the forecast, the itemised row and the cash book revenue line read one function; the test pins that the cash book revenue equals the itemised revenue. The price a new good fetches once sold is not forecast. Tests: `sim/tests/test_complaint_584_forecast_takings_cash_book.py`.
