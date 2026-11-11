# A thin unskilled labour market sets every trade's reservation wage, stops farming in its area, and leaves a neighbour hungry

**Status:** partly - the unskilled wage is an option only for the hours its jobs can take (`sim/labour/market/unskilled_reach.py`); measured on england_1300, hungry spin-up years fall to about a third, in count and in food short, and the first traced year is fed, but some remain

**What is wrong.** In England's spin-up, households on some partner tiles go short of food in single years while holding years
of income in cash. On the branch the spin-up has several such years, the worst short by a large share of the whole economy's
food floor; on main the same spin-up has one small one. The opening itself starts with no hunger (the measured window ends
on a fed year), so a new game looks fine, but the same rule can stop a whole trade at any time in play.

**Mechanism** (measured on england_1300 by probes over `sim/markets/port_trace.spin_up_trace`):

1. The area `work@france_05` has almost no workers of the unskilled (fallback) trade. In year 0 its market sells a handful of
   hours against a demand many orders larger, so it clears at its cap, far above the farm wage there.
2. `unskilled_option` (`sim/labour/market/clearing.py`) hands that start-of-year unskilled wage to every other trade in the
   area, and `clear_one` puts it into each trade's reservation (`reservation = max(..., option)`).
3. Every farm employer's maximum wage is below that reservation, so `_wage_with_supply` moves the farm wage toward it,
   `eligible_bids` drops every employer, and the area hires no farm hours in year 1. The farm, mill and bakery that supply
   the neighbouring tile (`germany_01`, whose grain markets are in the area `france_05@b2`) make nothing.
4. With no trade the year before, the tile's food markets have only a remembered price; `MarketMemory.offered_price` gives
   none for that kind, `households_basket.need_prices` drops the food need, and the households bid for no food. Their own
   plot output also falls, because `household_work_year.grinding_plan` keeps more hours at home when grain is unpriced.
   The food floor goes unmet.

On main the same unskilled wage spike happens, but per-employer contracts kept farm hours at their old wage
(`eligible_bids` with contracts, `contracted_wage`). Commit ebd549c ("One wage per trade and area; no per-employer
contracts") removed that buffer by design, and with it the test of contract rigidity.

**Why it matters.** A wage paid on a few hours is treated as an option open to every worker of every other trade, so a
single thin market can shut down a whole trade and the chains that depend on it. The hours that could really take the
unskilled jobs are only as many as that market still wants.

**Measure it.** Wrap `sim.economy.api.spin_up_state` to print `sum(outcome.hunger_by_tile.values())` each year, and run
`port_trace.spin_up_trace(game, years)` on a `Sim` built as `sim/ui/cli_spin_up_trace.py` builds one, for `england_1300`,
once on this branch and once on main. Four years reproduce the first hungry year in a couple of minutes.

**What was done.** The second option, as a mean ask: `clear_one` and the packed kernel (`clearing_kernel.market_heads`, cell
`JOBS`) no longer floor a trade's reservation at the whole start-of-year unskilled wage. The hours employers bid for the unskilled
trade at that wage or more (`ImportCosts.jobs_at`) are the jobs the option can take; the share of the trade's hours they cover
(`unskilled_reach.share_reaching_unskilled`) asks the unskilled wage and the rest ask the trade's own reservation, so the
reservation is the mean (`reservation_with_unskilled_option`). It is continuous in the jobs, unchanged where the unskilled
market has jobs for every hour of the trade or no option is stated, and a handful of hours at a spike wage no longer sets a
whole trade's reservation. Regression tests: `sim/tests/test_unskilled_reach.py` (the rule, a thin and a deep unskilled
market through `clear_all`, and the plain rule against the packed kernel).

**Measured (2026-11-11), with the wrapper below and a fresh spin-up cache, against the branch before the change:** fewer hungry spin-up years and about a third of the food short over the whole spin-up; the traced years after the opening are all fed, where before the second traced year was hungry. Hungry years remain in the later spin-up, so the rule is not the whole cause. No committed command runs this; it is the wrapper this paragraph names.

**What is left.** Find the cause of the remaining hungry years (the open questions below). The game measurement: wrap `sim.economy.api.spin_up_state` to print `sum(outcome.hunger_by_tile.values())`
each year and run `port_trace.spin_up_trace(game, 4)` on a `Sim` built as `sim/ui/cli_spin_up_trace.py` builds one, for
`england_1300`; the hungry years should be gone or as small as before the contract removal. If a hungry year remains, the
open questions below are next. The commit and branch this text once named are not in the repository.

Open questions found on the way: why `work@france_05` has almost no unskilled workers at the opening, and why the
branch's year-0 wages in some trades differ from main's.
