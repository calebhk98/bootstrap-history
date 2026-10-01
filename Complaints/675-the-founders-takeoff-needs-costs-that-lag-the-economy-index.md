# The founder's takeoff is the economy index raising takings while costs stand still; with pay following output it stalls

**Status:** open - found making what a firm carries follow the economy (Complaints 620, 600). Measure with `_fp`-style drivers: Rome seeds 1-3, recommended strategy, `Sim.state.economy.economy`, `Sim.labour_pay_scale()`, founder capital and `Sim.actors.active_firms()` per decade; `LABOUR_PAY_SHARE_OF_OUTPUT_GAIN` is the knob.

`Sim.market_wage_per_hour` is the wage table times `labour_pay_scale()`, one figure for founder, firms, state and households. Findings:

- With the share at one, or one half, none of Rome seeds 1-3 leaves debt in 100 years: the economy index stays between two and three and the founder holds a handful of concerns. With the share at zero (the default) all three take off, later than before the change. The founder's payroll is almost nothing early (a couple of staff), so the stall is not the payroll: it is what hiring and building labour cost the founder (project labour, finder's fees, wages advanced) rising with the index while his takings rise with it too and nothing makes research or building more productive.
- The takeoff before the change came from the index lifting every concern's takings while a concern's cost stayed put, so payback improved with every diffused technology: the loop of Complaint 104. Any treatment that scales costs with takings removes it, and this model has no other source of return on technology.
- The existing tightness mechanism cannot express aggregate scarcity: it moves trades against each other around the need shares, with total need equal to total hours, and is capped (`MIN_TIGHTNESS_FACTOR`, `MAX_TIGHTNESS_FACTOR`). Firm, founder and state demand for hands is a tiny share of the working population, so the free-pool limit (`free_fte`) binds long before a price could.
- Revenue is still derived at opening prices and scaled by the generic index (`287`), so it does not follow what the goods fetch.

What replaces the heuristic: aggregate demand for hands (every actor's staff plus the army) cleared against the working population, with takings that follow the market's own price and volume. Until then the share stays at zero and the pay scale is an off switch, with upkeep following volume sold carrying the firm count (620). Related: `104`, `287`, `600`, `620`.
