# The founder's capital grows tens of times in the late game, and nothing compares it with the economy it lives in

**Status:** partly - the comparison base was wrong and is fixed; the founder's wealth has no cap and no target, and pay that follows output stalls the takeoff so it stays off

Absorbed: 354 (the takeoff is the economy index raising takings while costs stand still; with pay following output it stalls).

## What is wrong

In a Rome seed-1 run with the recommended strategy the founder's capital rises steeply between years 100 and 150 (Han does the same on some seeds; some seeds stay near zero and others take off between years 75 and 100, so the outcome is bimodal). A founder who ends up owning more than the economy can produce, or whose wealth compounds with no market, tax or political limit, makes every late-game strategy look the same. Historically the richest private fortunes were a few percent of the economy's yearly output; that is a validation range, not a target.

Measured (Rome seed 1, recommended strategy, `_fp/measure.py`-style driver reading `Sim.household.money` against `SimWorld.society_output()`): about 3.6% of one year's society output at year 100 and about 11% at year 150 (peak near 18% at year 130), before the fix below. Giving firms the means to grow did not change it (345).

Diagnosis: `society_output()` was the working population at the opening unskilled wage, so it did not rise with the economy index, while the founder's takings rose with the index to the 0.75 power. The share rose with the index alone. The founder's income at takeoff is overwhelmingly concern margin (venture revenue), with interest and sales to the state small beside it (`cash_book.causes_since`). Fixed: `society_output` now multiplies by `output_volume_scale()` and the upkeep of a concern that sells follows its volume (345), so the share is measured against an economy that grows as his does. Re-measure the share per decade, Rome and Han, seeds 1-4.

## The takeoff and why pay following output stalls it (354)

`Sim.market_wage_per_hour` is the wage table times `labour_pay_scale()`, one figure for founder, firms, state and households. Knob: `LABOUR_PAY_SHARE_OF_OUTPUT_GAIN`. Measure with Rome seeds 1-3, recommended strategy, `Sim.state.economy.economy`, `Sim.labour_pay_scale()`, founder capital and `Sim.actors.active_firms()` per decade.

- With the share at one, or one half, none of Rome seeds 1-3 leaves debt in 100 years: the index stays between two and three and the founder holds a handful of concerns. At zero (the default) all three take off, later than before the change. The founder's payroll is almost nothing early, so the stall is what hiring and building labour cost the founder (project labour, finder's fees, wages advanced) rising with the index while his takings rise with it too and nothing makes research or building more productive.
- The takeoff came from the index lifting every concern's takings while a concern's cost stayed put, so payback improved with every diffused technology (the loop of 101). Any treatment that scales costs with takings removes it, and this model has no other source of return on technology.
- The tightness mechanism cannot express aggregate scarcity: it moves trades against each other around the need shares (total need equal to total hours) and is capped (`MIN_TIGHTNESS_FACTOR`, `MAX_TIGHTNESS_FACTOR`). Firm, founder and state demand for hands is a tiny share of the working population, so the free-pool limit (`free_fte`) binds long before a price could.
- Revenue is still derived at opening prices and scaled by the generic index, so it does not follow what the goods fetch (283).

## What it would take

Aggregate demand for hands (every actor's staff plus the army) cleared against the working population, with takings that follow the market's own price and volume; until then the pay scale stays an off switch and upkeep following volume carries the firm count (345). Then decide whether a remaining takeoff is a missing mechanism (saturation of the founder's own markets, taxation of visible wealth, interest groups pushing back: 311, 114) or a wrong one (revenue still authored: 283).

Related: 345, 101, 283, 311, 114.
