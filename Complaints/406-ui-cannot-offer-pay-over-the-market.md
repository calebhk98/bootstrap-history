# The player cannot offer pay over the market or see how many hands can be found

**Status:** open

`LabourMarket.quote(..., pay_premium)`, `quote_annual(..., pay_premium)`, `hire(..., pay_premium)` and
`recruitable(trade, people, pay_premium)` exist (sim/labour/labour_market_api.py). No command takes a
premium, and the hire screen does not show how many of the people asked for can be found this year.

What it would take (in `sim/ui/`):
- `hire <trade> <count> [premium%]` passes the premium through.
- The quote line shows `recruitable` beside the price.
- Both depend on Complaint 403 for the premium to be charged every year.
