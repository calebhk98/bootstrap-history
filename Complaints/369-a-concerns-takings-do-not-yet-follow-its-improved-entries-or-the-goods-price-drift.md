# A concern's takings do not yet follow the production entries it uses or the drift of its goods' prices

**Status:** open - found removing the economy index (Complaints 101, 112, 354). Takings of a concern are its authored revenue at its own volume, times the market's spot-over-long-run ratio for output-derived nodes (`node_output_market_factor`) and the goods-category share (`goods_market_factor`); no index scales volume any more, so the founder's takings stand still while real output rises.

What is missing, in order:
- A concern's volume per staff should follow the labour and materials of the production entries it uses (`sim/engine/node_output.py` already knows each entry's hours and plant), so a technique that halves an entry's labour doubles what the same staff turn out.
- Its takings should be that volume at the market's price now, not at the long-run price the tree loaded with times the ratio: when a technique cheapens the good, the long-run price falls and the concern's takings must fall with it (`node_revenue_market.market_factor` values baskets at load-time prices).
- With both, a founder only ahead of the society (a technique the society lacks) earns more; one the society already holds earns the competitive return. Today every technique the founder completes is held by the society at once (`done`), so there is no lead to earn.

Measure with `_fp/measure.py`-style drivers: Rome and Han, seed 1, 150 years: founder capital, `Sim.real_output_hours()`, firm count.

Related: 101, 112, 354.
