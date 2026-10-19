# Revenue forecasts and the cash book disagree with takings

**Status:** open

Found by an agent playtest (`Complaints/reports/playtest-rome-seed11-agent-to-221.md`, from 120 AD). `fin_lottery` was forecast at tens a year and took thousands;
in 139 AD the cash book booked several times the revenue the money breakdown itemised. 577 put quotes and takings
on one function for concerns not yet open; the lottery and the cash book's revenue line still disagree with it.

What it would take: the forecast, the yearly takings and the cash book's revenue line read one function each year
(screens and engine read one number); a test that a running concern's forecast for the year matches its takings
within the year's price change, and that the cash book's revenue equals the itemised revenue.
