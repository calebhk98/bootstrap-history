# Tax collection eats most of the state's coin revenue, and the state lends while it is short

**Status:** open

In a default Rome the `tax_collection` line costs nearly all the coin the state collects in year one, so the
state is underfunded every year and never builds a surplus. The cost comes from the
`*_BASE_PER_COLLECTOR_WAGE_YEAR` heuristics in `sim/agents/tuning_spending.py` priced at scribe pay.
Measure: open a game with `harness.sim()`, step a year, and compare the treasury's `tax_collection`
outlay with its coin revenue (`state_budget` and `state_surplus` topics set up such games; `state_surplus`
now gives its "stable" state a reserve to work around this).

The same state also makes loans ("loans made" in its outlays) while it has unfunded need and unpaid bids in the
book (`sim/economy/lending.py`), which overdraws its purse once the market clears.

Both need an owner decision on how collection should be costed and whether a short state may lend.
