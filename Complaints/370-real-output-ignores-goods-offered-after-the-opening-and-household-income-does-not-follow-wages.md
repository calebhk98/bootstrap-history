# Real output ignores goods offered after the opening, and household income does not follow wages

**Status:** open - found building real output (Complaints 101, 112). `Sim.real_output_hours()` values the quantities the market clears at the opening's prices over the opening's basket (`sim/engine/real_output.py`).

- A good households were not offered at the opening has no opening price, so a technique that makes a new good adds nothing to real output (labelled a temporary heuristic in `real_output.py`). A chained basket (re-based each year, quantity index linked) would count it.
- Household income is held at `MEAN_INCOME_HOURS_PER_CAPITA` in labour hours. Real income grows only as goods cost fewer hours. A wage that rises above the numeraire (the labour market's scarcity) should raise income and so demand: `sim/engine/labour_market_api.py` owns the wage and is being worked on separately.
- Society output no longer deducts soldiers under arms (it is the quantities cleared, which armies do not change).

Related: 101, 112, 369.
