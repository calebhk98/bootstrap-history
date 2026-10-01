# Firm count still climbs late in a run: a market grows with the economy, a concern's size and wage do not

**Status:** partly - firms now grow: a firm's concern has a capacity (`ActorRecord.capacity`, founding sizes, default one) and an incumbent whose added capacity earns more than the capital costs (the market rate from its purse, its own borrowing rate on what it borrows) adds up to `EXPANSION_RATE` of its size a year (`sim/engine/actors/firm_expansion.py`); takings, staff, wages, upkeep, supply and the category's seller count all follow capacity, and entrants expect the margin left after it. Rome seed 1 (recommended): 7581 firms at year 150 before, 3095 after; total staff in firms 3794 before, 10422 after; average firm 0.50 staff before, 3.4 after. Han (a handful of firms, economy not growing) is unchanged. The count is still thousands, because entry is limited only by its rate: `620`. Regression: `test_firm_expansion`. Measured with `_fp/measure.py`-style drivers (step the recommended-strategy game, read `actors.active_firms()` per decade).


Complaint 535 part 1 made entry bounded by the market: an entrant expects takings after its own and waiting entrants' supply (`goods_category_factor_with_entrants`), less upkeep and the staff's wages, and needs the margin to beat the civilisation's interest rate on its stake. Per niche that stops entry once a category's demand is shared out. What still grows the count:

1. A concern's takings scale with `economy ** ECONOMY_OUTPUT_SCALING_EXPONENT` while its upkeep, staff and the wage table do not, so as the economy grows by tens of times the market for a niche supports tens of times more identical firms. A real firm in a larger market grows (capacity, staff); here a concern has one fixed physical size.
2. Entry is at most one firm per proven concern per year, so a niche that can hold hundreds fills over decades, and every concern the founder proves adds a niche.
3. The pooled stake (`ENTREPRENEURIAL_CAPITAL_SHARE`) is a per-entrant ceiling, not a drawn-down savings pool; no entrant ever competes for the same capital.

Fix direction: let a firm's capacity scale with the market it serves (its output and staff, so wages and upkeep follow), or tie wages to the economy index. Re-measure with the driver before and after.
