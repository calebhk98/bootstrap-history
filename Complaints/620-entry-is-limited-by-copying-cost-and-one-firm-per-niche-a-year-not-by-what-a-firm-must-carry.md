# What caps the number of firms in a niche is the rate of entry, because a firm's fixed costs are a tiny share of what a market pays

**Status:** partly - what a concern must carry now follows the volume it sells and upkeep follows the volume sold, so firms grow more slowly than the volume they share (test `firm_costs_scale`); pay per hour following output stalls the founder's takeoff and is off by default (Complaint 675)

A firm's takings are the founder's concern takings scaled by `economy ** ECONOMY_OUTPUT_SCALING_EXPONENT`, shared by every seller in the goods category. What a firm must carry (upkeep, wages, the copy cost of its know-how) does not scale with the economy, so by the time the economy has grown tens of times the costs are a few percent of one seller's takings. An entrant needs only a positive margin that beats the capital it ties up at the market rate, so entry stays profitable until a category is shared out among very many sellers; what actually stops the count is the one-entrant-per-proven-concern-per-year rate limit, not the market.

Incumbents now expand (Complaint 550), which lowers the count for the same market, but an entrant and an expanding incumbent see the same unit margin and the incumbent also pays for the price it lowers on its own earlier capacity, so entrants keep arriving wherever any unit margin remains.

What is missing is a cost a firm must carry whatever its size and that grows with the market it serves: management and administration (Complaint 550's span-of-control exponent is a labelled stand-in), the licences and levies a visible firm owes, the rent on a site, and the wage table following the economy (labour is the scarce input, so a richer economy pays more per hour; see `Complaints/287`, `462`). Once those exist the number of firms per niche follows from the market and the cost of a minimum efficient size, and the rate limit stops being the binding one.

Related: `535`, `550`, `471`, `185`, `600`.

Done (firm-costs-scale): `Sim.output_volume_scale()` is the one volume factor takings use, and `concern_running_scale` applies it to the upkeep of a concern that sells (founder, `venture_real_upkeep`, and actors, `SimWorld.upkeep`): inputs are bought per unit sold. `Sim.market_wage_per_hour` is the wage table times `labour_pay_scale()`, one figure for every employer; its share `LABOUR_PAY_SHARE_OF_OUTPUT_GAIN` is zero by default because above zero the founder's takeoff stalls (Complaint 675). With it at zero only upkeep follows the volume, so wages (a rising share of a firm's cost late) still lag it. Measure: `python3 sim/test_regressions.py --only firm_costs_scale`, and firms per decade with `Sim.actors.active_firms()` on Rome seed 1.

Not done: a site rent, management or visibility levy as its own size-dependent cost (the span-of-control exponent of Complaint 550 is still the only one), pay that follows output (Complaint 675), and the rate limit of one entrant per proven concern a year.
