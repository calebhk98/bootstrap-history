# Firm count still climbs late in a run: a market grows with the economy, a concern's size and wage do not

**Status:** partly - firms grow (see earlier), and now a firm in a crowded market must also carry a fixed entry premium and leaves when it earns less than its plant would lend for, which slows the count at the same market size. Measured with a driver that seeds 22 proven founder concerns in a Rome run (agent_economy off) and scales the economy's output factor by 5% a year (about 130x at year 100), counting `actors.active_firms()`: year 100 firms 871 / staff in firms 725 / average size 0.83 before, 387 / 646 / 1.67 after; year 70: 490 / 317 / 0.65 before, 214 / 280 / 1.31 after (the count was still climbing before; it climbs more slowly after).


Complaint 330 part 1 made entry bounded by the market: an entrant expects takings after its own and waiting entrants' supply (`goods_category_factor_with_entrants`), less upkeep and the staff's wages, and needs the margin to beat the civilisation's interest rate on its stake. Per niche that stops entry once a category's demand is shared out. What still grows the count:

1. A concern's takings scale with `economy ** ECONOMY_OUTPUT_SCALING_EXPONENT` while its upkeep, staff and the wage table do not, so as the economy grows by tens of times the market for a niche supports tens of times more identical firms. A real firm in a larger market grows (capacity, staff); here a concern has one fixed physical size.
2. Entry is at most one firm per proven concern per year, so a niche that can hold hundreds fills over decades, and every concern the founder proves adds a niche.
3. The pooled stake (`ENTREPRENEURIAL_CAPITAL_SHARE`) is a per-entrant ceiling, not a drawn-down savings pool; no entrant ever competes for the same capital.

Fix direction: let a firm's capacity scale with the market it serves (its output and staff, so wages and upkeep follow), or tie wages to the economy index. Re-measure with the driver before and after.

Related: 341, 354.
