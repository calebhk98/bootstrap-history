# The opening's income leaks saving, so the economy opens at subsistence and its wage keeps falling

**Status:** open - umbrella (stationary solver started, 473 Update 6); the plan is carried by 606, 605, 608, 607 (closes when they do); measurement history in `Complaints/reports/526-history.md`

**What is wrong now.** The opening sets household income as the fixed point of income and the demand it pays for
(`sim/economy/opening_income.py`). Households save part of any surplus and nothing in the fixed point spends that saving
(no investment demand), so the fixed point falls toward the cost of the households' floors: every opening is a stationary
near-subsistence economy. Several fixtures state a household income through `EconomySetup.opening_income_per_head` to get
households with a surplus. During the spin-up the labour market clears at the households' outside option, far below the
cost-table wage, so wage and price level fall for decades and no spin-up settles. Measure:
`python3 sim/simulator.py opening-checks`; `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`.

Why it matters (CLAUDE.md 4.1, 4.2): a society's surplus over subsistence follows from its productivity, not from a
stated income; an opening that drifts for decades makes every number a player sees depend on when the spin-up stopped.

**Cause measured.** The savings wish in `households_orders.goods_orders`, not satiation: the wealth a cohort wants to keep is
many times its income, so spending falls toward the floors and the rest goes to `funds_offers`. Counting held durables and
land does not close it (land earns no capitalisable rent without plot titles, 538); the opening's firm equity lifts the
settled income by about a third and no more. The wish is far larger than any wealth households hold.

**What it would take** (order of work, each a child):

1. 606: source or shrink the savings wish (a labelled figure with no source).
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
- Lowering `SAVINGS_RESPONSE_FLOOR`: only reaches the ceiling at a rate nobody lends at; the floor stays.
- Counting durables and land as held wealth: settled income barely moved.
- Correct accounting (546, 547) moved where the spin-up's drift stops; the shipped openings cannot be regenerated
  (`python3 sim/simulator.py openings` refuses failing checks) until this is fixed or the failure is shipped with
  `--allow-failing REASON`.
