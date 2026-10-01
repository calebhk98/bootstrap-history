# Firms multiply into the thousands: what caps a niche is the rate of entry, because a firm's fixed costs are a tiny share of what a market pays

**Status:** partly - entry is bounded by the market, incumbents expand, and what a concern carries follows the volume it sells; the count is still thousands by year 150 because nothing a firm must carry grows with the market it serves

Absorbed: 330 (entry has no ceiling; the state's military relief per weapon) and 331 (a market grows with the economy, a concern's size and wage do not).

## What is wrong

A firm's takings are the founder's concern takings scaled by `economy ** ECONOMY_OUTPUT_SCALING_EXPONENT`, shared by every seller in the goods category. What a firm must carry (upkeep, wages, the copy cost of its know-how) does not scale with the economy, so once the economy has grown tens of times the costs are a few percent of one seller's takings. An entrant needs only a positive margin that beats the capital it ties up at the market rate, so entry stays profitable until a category is shared out among very many sellers. What stops the count is the rate limit (one entrant per proven concern per year, and every concern the founder proves adds a niche), not the market. The pooled stake (`ENTREPRENEURIAL_CAPITAL_SHARE`) is a per-entrant ceiling, not a drawn-down savings pool, so entrants never compete for the same capital (see 106). Late in a run the yearly actor turn is the dominant cost (321).

Measure: step the recommended-strategy game on Rome seed 1 (a `_fp/measure.py`-style driver) and read `Sim.actors.active_firms()`, firm concerns, inventions the government holds and founder capital per decade; Han has a handful of firms and an economy that does not grow, so it is unchanged by all of the below.

## Built

- Entry (330 part 1): an entrant expects its takings after its own output and the waiting entrants' reach the shared market (`goods_category_factor_with_entrants`), less upkeep and the staff's wages, and must beat the market rate on its stake; firms pay the wages they ignored.
- Incumbent expansion (331; `sim/engine/actors/firm_expansion.py`, `ActorRecord.capacity`, `EXPANSION_RATE`, founding sizes default one): an incumbent whose added capacity earns more than its capital costs (market rate from its purse, its own borrowing rate on what it borrows) adds capacity; takings, staff, wages, upkeep, supply and the category's seller count follow it. Rome seed 1: 7581 firms at year 150 before, 3095 after; staff in firms 3794 before, 10422 after; average firm 0.50 staff before, 3.4 after. Regression: `test_firm_expansion`. Per-year CPU barely moved (321).
- Costs follow volume (`firm_costs_scale`): `Sim.output_volume_scale()` is the one volume factor takings use, and `concern_running_scale` applies it to the upkeep of a concern that sells (founder `venture_real_upkeep`, actors `SimWorld.upkeep`). `Sim.market_wage_per_hour` is the wage table times `labour_pay_scale()`; its share `LABOUR_PAY_SHARE_OF_OUTPUT_GAIN` is zero by default because above zero the founder's takeoff stalls (341). Measure: `python3 sim/test_regressions.py --only firm_costs_scale`.
- The state's war relief is per weapon (330 part 2): `STATE_MIL_RELIEF_PER_WEAPON_OUTPUT` and `STATE_MIL_RELIEF_PER_WEAPON_SACK`, each of the founder's military nodes the government holds removes its share of what is left, and inventing more weapons never lowers it (`test_state_weapon_relief`).

## What it would take

A cost a firm must carry whatever its size that grows with the market it serves: management and administration (331's span-of-control exponent is a labelled stand-in and the only one), the licences and levies a visible firm owes, the rent on a site, and wages following the economy (labour is the scarce input; pay that follows output is parked in 341, see also 283). Entrants and an expanding incumbent see the same unit margin and the incumbent also pays for the price it lowers on its own earlier capacity, so entrants keep arriving wherever any unit margin remains. With those costs in, the number of firms per niche follows from the market and the cost of a minimum efficient size and the rate limit stops binding. Firms raising their stake from the loanable-funds market (106) would slow entry when funds are dear.

Related: 341, 321, 181, 106, 101.
