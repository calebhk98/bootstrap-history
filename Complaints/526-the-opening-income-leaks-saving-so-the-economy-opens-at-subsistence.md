# The opening's income leaks saving, so the economy opens at subsistence and its wage keeps falling

**Status:** partly - umbrella; the savings wish is gone (spending follows Eurace's consumption budget) and the opening rests under the first year's rules, but the income fixed point still has no use for saving; the plan is carried by 606, 608 and 607 (605 is closed; it closes when they do); measurement history in `Complaints/reports/526-history.md`

**What is wrong now.** The opening sets household income as the fixed point of income and the demand it pays for
(`sim/economy/opening_income.py`). Households save part of any surplus and nothing in the fixed point spends that saving
(no investment demand), so the fixed point falls toward the cost of the households' floors: every opening is a stationary
near-subsistence economy. Test fixtures state a surplus through `surplus_households` (607). During the spin-up the labour market clears at the households' outside option, far below the
cost-table wage, so wage and price level fall for decades and no spin-up settles. Measure:
`python3 sim/simulator.py opening-checks`; `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`.

Why it matters (CLAUDE.md 4.1, 4.2): a society's surplus over subsistence follows from its productivity, not from a
stated income; an opening that drifts for decades makes every number a player sees depend on when the spin-up stopped.

**Cause now.** Household spending is Eurace@Unibi's consumption budget (`households_buffer_stock.spending_budget`, called from
`households_orders.goods_orders`): mean net income plus a yearly share of cash and claims plus a share of share wealth above a
target. The savings wish this complaint was filed against no longer exists. What still leaks: `opening_income.settled_income_per_head`
finds the largest income at which households save nothing net, and nothing in the final demand spends saving (no plant,
working capital or lending demand is counted), so the fixed point stays at the cost of the households' floors unless a
fixture states an income. The opening's stocks are solved to rest under the first year's rules (`opening_resting.py`:
capacity at planned output, output stock at target, household purse from owned shares to the target wealth) and its income is
limited by what the working hands can make (`opening_income.producible_share`). Whether the spin-up now settles is 473's, and
has not been re-measured here.

**What it would take** (order of work, each a child):

1. 606: source the stored figures of the consumption budget (the wish is gone; the Eurace constants have no pre-modern source).
2. 605: an `equity(agent)` on the market view, so the opening's wealth wish is set against what households own.
3. 538: land and plot titles carry a value (the asset the probes found missing).
4. 608: the opening wage is the value of labour's marginal product, consistent with the households' outside option, not the
   coin metal's table cost.
5. 607 and 545 land together (545 cannot land alone: own-plot growth in the fixed point drives the settled income to zero while
   the leak stays); then delete `opening_income_per_head` and its fixtures. The wage drift is 473.

Tests wanted: realised year-0 income within a band of the opening figure; the spin-up settles; a more productive technique
set opens with a larger surplus.

**Tried and why it failed.**

- An opening rate search (branch `fix-526-opening-rate`, not merged; `sim/economy/opening_rate.py` is not in main): lifted
  settled income by about a third then flat, and the wage drifted lower than without it, so the rate is not what drives the wage.
- Counting durables and land as held wealth: settled income barely moved.
- Correct accounting (546, 547) moved where the spin-up's drift stops; the shipped openings cannot be regenerated
  (`python3 sim/simulator.py openings` refuses failing checks) until this is fixed or the failure is shipped with
  `--allow-failing REASON`.

## Update: does more money reach prices?

Measured before the Eurace household spending, labour offer and price rules; the savings wish and the leisure anchor named below no longer exist, so re-measure before relying on the figures. (branch money-reaches-prices; `economy_state_budget_validation`, `state_debasement_prices_scenario`)

Traced on the opened England economy (declared-length opening, fiat, `issue` only; the probes were throwaway scripts, not
committed) and on the Rome two-game debasement scenario. Command for the validations:
`python3 -m sim.tests --slow --only TOPIC --jobs 1 --topic-seconds 290`.

**Where the coin goes.** The state's programme is a stated real target of a multiple of the money stock a year; the economy's
own goods sales are about a tenth of that stock a year. So a printing of four times the stock is about forty times the year's
sales, bought as quantities at any price, and the coin reaches sellers of the few goods the state buys, not every seller.
Households spend roughly their income (spending over cash held is about a tenth a year in every run, printed or not), so the
stock they hold grows with the printing and does not come back as demand; velocity (goods sales over the money stock) is
about a tenth to a third a year in the control and falls as the stock rises. Of the coin printed, the labour channel spent
almost none of its plan: the state bids at most one and a half times last year's wage for at most a share of each tile's hours,
and vacant hours stayed in the tens of millions per tile while the state hired a few million. The unspent wage plan stayed in
the state's purse (about 45 percent of the money stock after four years at sixteen times).

**Why the levels were absurd** (measured, `opening_basket` value shares at base prices): `glass_raw_kg` is 77 percent of the
basket's value (5.5 million kg at 2360 a kg, as the vessels need's floor is met mostly by glass), against about four percent of
what the market actually trades in basket goods (`traded_spending_weights` on the opened record: ceramic 47 percent, piped water
16, iron tools 6). The weighted median that chains the level (`currency.price_inflation`, read by the state's programme, the
leisure anchor and the households' perceived level) is therefore glass's own price change alone, and the control already ran
0.71, 1.28, 0.95, then 54 in four years on one thin good. At sixteen times the printing, flour and wheat rose over a hundredfold
and bread tenfold while the level read 0.55, so the state's nominal budget (target times that level) fell as prices rose.
The fixed-basket level (what the validation read) is carried by thin goods with a few tenths of a percent of the weight
(brick walls 370 thousand times base, milk 49 thousand): 4342 for the smaller printing and 562460 for the larger in the run the
task named, a different pair in each run, so it orders nothing. 473 Update 9 recorded both ("weights in `price_inflation` use each good's
full opening quantity"; the fixed-basket level "still wanders over an order of magnitude").

**Fixed (rule tests on built inputs).**
- `national_prices.traded_spending_weights`, used by `year_close.remember_basket_price_level`: the median's weights are last
  year's traded volume times price over the basket goods, falling back to the opening basket only until goods trade.
  Test: `sim/tests/test_price_inflation_weights.py` (a good that dominates the opening basket and barely trades does not set
  the inflation).
- `state_budget.lapse_unspent_wages`, called after the labour market clears: a stated real programme that could not hire what
  it planned spends the remainder on goods (a shortage of hired labour must not leave printed coin in the purse). Test:
  `sim/tests/test_state_unspent_wages.py`.
- `economy_state_budget_validation` now reads the chained level (`memory.price_levels`) instead of the fixed-basket one. This
  changes which reader is measured, not a bound: every threshold is as it was.

**Measured after (same opened economy, hash seed fixed; control, four times, sixteen times the stock a year, years 0 to 3):**
the chained level, control 0.98, 0.98, 0.90, 0.97; four times 2.75, 11.5, 10.1, 10.3; sixteen times 3.0, 13.5, 15.3, 11.9. Before
(same reader weights, old rule): control 0.71, 1.28, 0.95, 54; four times 0.71, 1.37, 1.90, 1.39; sixteen times 0.71, 0.87, 0.71,
0.55. Printing now raises the level about tenfold in four years; the larger printing raises it 1.16 times the smaller, not the 1.25 the
check asks for, so `printing_more_raises_the_price_level_more_instead_of_saturating` is still red (11.94 against 12.92), and the
runaway check misses its twentyfold bound narrowly (53.9 against 67.4, the first year already carrying a 2.7 times rise).
Balanced-budget share check is green on this head (it was red on the base).

**What is left, and what the premise needs.** The remaining saturation is physical or a stated heuristic, not a wrong
reader: the state buys quantities in markets whose supply cannot respond (thin goods carry the rise, the median goods do not),
its purse still holds about a fifth of the stock at sixteen times, and households hold what they receive (their spending follows
income). The quantity theory (price level proportional to money at stable velocity and fixed output) holds in the long run once
households' cash is back at its target; here households hold far more than the target of a quarter year of spending (the
leak this complaint is about), so velocity is a tenth to a third and falls as money rises, and a four-year window is
not long run. A validation that wants a proportional rise needs the money to arrive as income across households (a transfer or a
wage bill the labour market can fill), not as a purchase programme of forty times the year's output.
Tried and removed: scaling the households' smoothing band for the spending they may add in a year (`SPENDING_CUT_LIMIT`) by
expected inflation. It made the unprinted control deflate to 0.40 in four years (the symmetric rule cuts spending when prices
fall) and did not lift the printed levels.

**Debasement scenario.** The Rome pair (cut half the metal each year, three years), final head against its twin at year 3: coin in
circulation 1.27 times, fixed-basket level 1.88 against 1.54 (1.22 times), chained level 2.24 against 1.00; the check's bound is 1.05 on
the fixed-basket level and holds (220 s). On the base head the basket pair was 1.79 against 1.45 (1.24 times), chained 1.29 against
0.92: the effect is well clear of the edge in either run, but it is one seed of a draw (the fixed-basket level moves several tens of
percent between years on thin goods); the chained level, now weighted by trade, shows it more strongly.

Test migration (rule-tests-04): `economy_state_budget_validation` is deleted (the state's coin share steadying, printing raising the chained price level
and expectations, more printing raising it further: each read the opened England economy over years and could not name a rule). Printing adds exactly the
deficit to the supply and the state's purse in `test_economy_agent_state`. `python3 sim/simulator.py economy-check --civs england_1300 --years 8` prints
the price level and money supply by year.
