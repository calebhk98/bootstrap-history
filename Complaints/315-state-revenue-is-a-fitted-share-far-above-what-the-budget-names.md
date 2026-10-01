# State revenue is a fitted share of labour value, several times what the modelled budget spends

**Status:** open - found closing 286; next: derive revenue from what can be collected, or add the lines a real state spends the rest on

`SimWorld.state_revenue` is the working people not under arms, at the unskilled wage, times the economy's output factor, times `starting_tax_share` times state capacity. With the standing lines of 300 built (army, officials, roads, public buildings, court, dole, navy), a healthy Rome spends about a third of that and Han about a sixth, so neither goes short until a plague, a collapse of output or a threat-driven army takes the revenue below need. Measure: `python3 sim/budget_series.py rome_100ad 200 1` and the same for `han_china_100ad`; the table shows revenue beside the need by line. With `BUDGET_SERIES_IDLE_FOUNDER=1`, Rome goes short from the third-century crisis on and Han never does; Norse runs close to balance from the start.

Two ways to close it, and the second is the honest one. Spending that the budget does not name (campaigns beyond the standing force, building beyond upkeep, gifts to the army, tax collection itself) has no line of its own: a reserve above `RESERVE_CEILING_YEARS_OF_NEED` now hires public works and is lent through the capital market (`government_surplus.py`, 499, 412); each unnamed purpose still wants a physical basis. Revenue itself is a share of labour value at one wage, not of a taxable surplus (rent, trade, the harvest after subsistence); it should follow what can be collected.

All the new line sizes (`tuning_spending.py`) are labelled heuristics, so the ratios above move with them; do not treat the ratios as findings about Rome or Han.
