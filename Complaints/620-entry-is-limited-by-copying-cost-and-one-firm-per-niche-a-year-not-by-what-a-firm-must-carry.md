# What caps the number of firms in a niche is the rate of entry, because a firm's fixed costs are a tiny share of what a market pays

**Status:** open - found while giving incumbents the means to grow (Complaint 550). Measure with `_fp`-style drivers: Rome seed 1, recommended strategy, `Sim.actors.active_firms()`, `rivals_of`, per decade, and `python3 sim/test_regressions.py --only firm_expansion`.

A firm's takings are the founder's concern takings scaled by `economy ** ECONOMY_OUTPUT_SCALING_EXPONENT`, shared by every seller in the goods category. What a firm must carry (upkeep, wages, the copy cost of its know-how) does not scale with the economy, so by the time the economy has grown tens of times the costs are a few percent of one seller's takings. An entrant needs only a positive margin that beats the capital it ties up at the market rate, so entry stays profitable until a category is shared out among very many sellers; what actually stops the count is the one-entrant-per-proven-concern-per-year rate limit, not the market.

Incumbents now expand (Complaint 550), which lowers the count for the same market, but an entrant and an expanding incumbent see the same unit margin and the incumbent also pays for the price it lowers on its own earlier capacity, so entrants keep arriving wherever any unit margin remains.

What is missing is a cost a firm must carry whatever its size and that grows with the market it serves: management and administration (Complaint 550's span-of-control exponent is a labelled stand-in), the licences and levies a visible firm owes, the rent on a site, and the wage table following the economy (labour is the scarce input, so a richer economy pays more per hour; see `Complaints/287`, `462`). Once those exist the number of firms per niche follows from the market and the cost of a minimum efficient size, and the rate limit stops being the binding one.

Related: `535`, `550`, `471`, `185`, `600`.
