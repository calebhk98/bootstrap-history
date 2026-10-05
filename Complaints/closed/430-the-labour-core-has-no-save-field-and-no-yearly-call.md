# The labour core has no save field and no yearly call, so the founder's labour cannot use it

**Status:** closed - folded into 428

`sim/labour/market/` runs a year of a labour market:
- wages per trade and place
- entrants choosing trades by lifetime pay and their ability
- switching
- migration along routes
- apprenticeship and school pipelines
- employers who pay over the market

Nothing in the engine keeps its `MarketState` or calls `sim.labour.api.run_labour_year`, and labour
cannot add either from inside its package.
- `sim/engine/state.py` and `sim/agents/household.py` hold every saved field.
- `sim/engine/core.py:1528` calls only `labour.update_wages()`.

So the household-side verbs still read the older mechanisms:
- the tightness factor in `sim/labour/wages.py`
- the pressure curve in `labour_market_api.py`
- the supply estimate in `labour_population.py`

What is missing, all outside `sim/labour/`:
- A saved field, for example `EconomyState.labour_market: dict` holding `market_state_to_plain(...)`.
  It isn't needed if Complaint 428 puts the state in the agent economy's record instead.
- A yearly call that builds `YearInputs` and stores the new state.
  - Bids come from every actor's staff and concerns.
  - Subsistence and entrants come from demography.
  - Schools come from every actor's schools.
- Household fields the founder verbs need:
  - `pay_premium_by_trade`, so a premium chosen at `hire` is charged every year in `wage_bill`;
  - each trade school's founding year, or its trainee cohorts, so `found_trade_school` produces graduates
    after the training years instead of instant supply (`labour_population.found_trade_school`,
    `trade_schools` is `{trade: seats}` today).
- `LabourMarket.recruitable(trade, people, pay_premium)` already answers how many can be found this year
  (recruitment friction, Complaint 271). `hire` should take only that many once the above exists.
