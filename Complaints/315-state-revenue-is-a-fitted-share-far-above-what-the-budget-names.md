# State revenue is a fitted share of labour value, several times what the modelled budget spends

**Status:** partly - revenue is the declared forms assessed on modelled bases, in coin or in kind (test state_revenue_forms); remaining: a healthy state still runs a large surplus because spending it does not name has no line, and the bases are thin (no rent or land value, little foreign trade, coin as the only wealth)

`SimWorld.state_revenue` is the working people not under arms, at the unskilled wage, times the economy's output factor, times `starting_tax_share` times state capacity. With the standing lines of 300 built (army, officials, roads, public buildings, court, dole, navy), a healthy Rome spends about a third of that and Han about a sixth, so neither goes short until a plague, a collapse of output or a threat-driven army takes the revenue below need. Measure: `python3 sim/budget_series.py rome_100ad 200 1` and the same for `han_china_100ad`; the table shows revenue beside the need by line. With `BUDGET_SERIES_IDLE_FOUNDER=1`, Rome goes short from the third-century crisis on and Han never does; Norse runs close to balance from the start.

Two ways to close it, and the second is the honest one. Spending that the budget does not name (campaigns beyond the standing force, building beyond upkeep, gifts to the army, tax collection itself) has no line of its own: a reserve above `RESERVE_CEILING_YEARS_OF_NEED` now hires public works and is lent through the capital market (`government_surplus.py`, 327, 307); each unnamed purpose still wants a physical basis. Revenue itself is a share of labour value at one wage, not of a taxable surplus (rent, trade, the harvest after subsistence); it should follow what can be collected.

All the new line sizes (`tuning_spending.py`) are labelled heuristics, so the ratios above move with them; do not treat the ratios as findings about Rome or Han.

Related: 287, 314.

Owner decision (2026-10-02): should be fixed from actual values: a state can have several revenue forms (land, wealth, trade on imports and exports, people), often paid in kind (a share of food), not only coin.

Built (owner decision 2026-10-02): each civilisation declares `state_revenue` forms (basis, rate, optional `paid_in`, source) in its file; `sim/agents/revenue.py` assesses them on bases in `revenue_bases.py` (harvest, adult labour years, imports, exports, coin stock); in-kind revenue enters the state's stores and is used by its lines or sold through the goods market (`government_stores.py`). `starting_tax_share` no longer sets state revenue. Open: most rates are labelled placeholders (confidence D in the data); the surplus against the named lines persists (`python3 sim/budget_series.py rome_100ad 100 1`); the grain valuation follows the goods market's spot quote, which swings in some runs, so land tax in coin's worth swings with it (same command, Han).
