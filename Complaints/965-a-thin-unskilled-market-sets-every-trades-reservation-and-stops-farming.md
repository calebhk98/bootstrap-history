# A thin unskilled labour market sets every trade's reservation wage, stops farming in its area, and leaves a neighbour hungry

**Status:** open - a regression from branch economy-labour-single-source-cleanup (commit ebd549c); a fix was drafted and measured, not merged

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

**What it would take.** Three options were weighed:

- Count the unskilled wage only at the chance a switcher is hired at it. A draft on branch fix30-unskilled-option
  (`sim/labour/market/unskilled_chance.py`) removes the first hungry year, but its chance jumps from one to a fraction as
  the unskilled market passes from supplied to short, so near balance a trade's reservation would flip year to year.
- Split the trade's supply: the hours that the unskilled market's unfilled demand can absorb ask the unskilled wage, the
  rest ask their own reservation. Continuous, and unchanged where the unskilled market is supplied.
- Drop the unskilled floor from the clearing and leave moves between trades to the yearly switching rule
  (`sim/labour/market/switching.py`), which already moves workers toward better pay: one rule for one fact.

Open questions found on the way: why `work@france_05` has almost no unskilled workers at the opening, and why the
branch's year-0 wages in some trades differ from main's.
