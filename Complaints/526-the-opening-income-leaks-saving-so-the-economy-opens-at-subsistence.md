# The opening's income leaks saving, so the economy opens at subsistence and its wage keeps falling

**Status:** open

Found in 507 Stage 2 (merged). The opening sets household income as the fixed point of income and the demand it pays
for (`sim/economy/opening_income.py`). Households save part of any surplus, and nothing in the fixed point spends
that saving (no investment demand: producers building plant, lenders lending it on), so the fixed point falls to the
cost of the households' floors: every opening is a stationary near-subsistence economy, and the old opening's
surplus and growth are gone. Several fixtures now state a household income through a new setup input,
`EconomySetup.opening_income_per_head`, to get households with a surplus.

During the spin-up the labour market clears at the households' outside option, far below the cost-table wage, from
the first year; prices follow the wage down slowly while employment grows into the gap, so the wage and the price
level fall for decades and no civilisation's spin-up settles (`python3 sim/simulator.py opening-checks`; trace:
`python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`). Rome's unskilled wage ends below its floor.
The opening wage still comes from `wage_schedule` (anchored on the coin metal's table cost), not from what labour
can earn at the households' own work.

Why it matters (CLAUDE.md 4.1, 4.2): a society's surplus over subsistence follows from its productivity, not from a
stated income; and an opening that drifts for decades means every number a player sees depends on when the
spin-up stopped.

What it would take: the opening's income is the value of what its workers produce at opening prices, with saving
matched by investment (producers' plant and working capital, and lending) so the fixed point does not leak; the
opening wage is the value of labour's marginal product, consistent with the households' outside option, so the
labour market clears near the opening wage in year one. Then delete `opening_income_per_head` (a stated income is
an outcome, CLAUDE.md 4.1) and remove the fixtures' use of it. Tests: realised year-0 income is within a band of
the opening figure; the spin-up settles; a more productive technique set opens with a larger surplus.

## Found fixing 546 and 547

Correct accounting moves the opening: with only principal no longer counted as income (547),
`full_length_opening_checks` fails England's money against coin wear (by a small margin) and two sited-ore
price checks; adding producers that run only what their cash pays for, with working-capital loans (546),
clears the ore checks but leaves the Norse unskilled wage below its floor. Each change moves where the
spin-up's drift stops, which is this issue and 473, not a defect in the change. Measure with
`python3 -m sim.tests --slow --only full_length_opening_checks --topic-seconds 3000`. The shipped
openings cannot be regenerated (`python3 sim/simulator.py openings` refuses failing checks) until the opening
is fixed here, or the failure is shipped with `--allow-failing REASON`.

545 cannot land alone: with own-plot growing in the opening's fixed point (branch
`fix-545-opening-grows-its-own`), Rome's food floor is all grown at home, nothing left in market demand is a
floor, and the leak this issue names drives the settled income toward zero. The two are one fix.

## Measured cause: the savings wish, not satiation

In `data/world/needs.json` only a few needs carry a satiation limit
(ornament, seasoning, water, light, amusement); food, shelter, clothing, implements, warmth and the rest do not, and
`apply_satiation` moves the freed spending to them by budget weight. On a Rome opening, for each cohort at the
full-employment income, `need_basket.need_units` places spending equal to the whole income (spending over income is
one, per need shares sum to one). So "wanted income" built from satiated spending is unbounded, and hours that
follow it would not change.

What cuts the spending is the savings wish in `households_orders.goods_orders`: at the opening `_opening_bids`
gives the cohort cash equal to its income, the wealth it wants to keep (cash buffer plus years of surplus income)
is many times that, so the drawdown is negative and bounded only by income, and spending falls toward the floors
while the rest goes to `funds_offers`. The share lost grows with the surplus (the richest cohorts spend least).
Reproduce: build Rome as `probe526.py` does, set each cohort's `last_year_income` through
`opening_income.with_income`, and compare `sum(bid.budget)` of `households.goods_orders(cohort, ..., cash,
income, ...)` against income for `cash = income` and for larger cash; then trace
`opening_income.settled_income_per_head` pass by pass (value of demand over income per head rises toward one only as
income falls toward the floors). The fixed point therefore is the original leak of this issue (saving that nothing
spends) acting through the savings target, not satiation, and a target-income hours rule has nothing to bite on
unless needs get physical limits (food in calories) or the savings wish is matched by an investment demand.
Directions that follow from this: open households holding the wealth they want (their savings wish already met, so
the opening's bids spend income), and give saving a user (producers' plant and working capital, lending).

## Measured: counting what households already hold does not close the leak

Tested whether the wealth households already hold (durables in use, land) covers the wealth the savings wish wants.
No command in the repo measures this (a throwaway probe built Rome, opened it and compared each cohort's wanted
savings with what it holds; the probes are not kept). Findings on Rome without a spin-up:

- Land is negligible. The opening pays no rent yet; clearing the land market for the producers the opening
  sizes gives a rent whose capitalised value (rent over the opening rate) is a few hundredths of a year of
  household income. Households pay no rent on their own plots, so the land they work earns nothing to
  capitalise; counting it needs plot titles with an imputed value (538), not a rent stream.
- Durables in use are real but uneven. Summed over cohorts they come near the wanted wealth, but cohort by
  cohort most hold about a third of the savings wish and a few (the city tile) many times it, which a cap at the
  savings target cannot use. Counting `min(savings, durables)` covers a bit over half of the wish in total.
- Effect on the fixed point: with each pass counting the durables the cohort would hold (the stock wanted at
  that pass), the settled income over the full-employment ceiling barely moves (from about 0.155 to about
  0.166). The hypothesis is false: the savings wish is far larger than any wealth a household holds, and
  counting held wealth does not remove it.

Not built. Direction that remains: give saving a user (producers' plant and working capital, lending), or make
the opening's wish match what the opening households hold.

## Built and measured: the opening finds its rate (branch `fix-526-opening-rate`); the drift remains

`sim/economy/opening_rate.py` finds the rate at which households' funds offered (their goods orders at the
full-employment income) equal the loans borrowers ask for (producers' working capital beyond the cash they
hold, merchants' cargo credit, queued requests such as the state's). The civilisation's `rate` is the search's
upper bound and starting guess; the lowest rate lenders accept (time preference plus expected inflation, and
the credit market's floor) is its lower bound. `open_economy` opens once to measure, then opens again at the
found rate. The result is kept in `record.opening_credit` (rate, whether it cleared, saving, requests).
When saving exceeds requests at every rate the search covers, it reports `clears: false` and opens at the
lowest rate; that is the case that needs an asset to buy (538). A stated income
(`opening_income_per_head`) skips the search; the fixtures that state a surplus keep the data rate.

Measured (settled income over the full-employment ceiling, no spin-up; `PYTHONPATH=. python3 <probe>` building
`build_setup(unopened_sim(civ="rome_100ad"))`, then `opening.open_economy`):

- Rome: rate 0.12 (data) opens at 0.21 of the ceiling with the replacement pass counted as before; the
  search finds a clearing rate of about 0.064 (saving and requests within 0.5%), where it opens at about 0.27
  to 0.31 (the two probe runs differ in the replacement pass). Held at fixed rates: 0.12 gives 0.21, 0.08 gives
  0.28, and 0.064, 0.05, 0.03, 0 give 0.27 each. The gain is about a third and then flat.
- Small fixture: no clearing rate (saving at full employment is several times the requests at every rate),
  opens at the lowest rate, settled income over the ceiling 0.0866 before and 0.0868 after.

Why the rate cannot do more: `SAVINGS_RESPONSE_FLOOR` (1.0) holds the wish at the base (two years of surplus
income) for every real rate below time preference, so below the lowest rate lenders accept the wish is flat and
no rate there could clear. Lowering the floor was measured (Rome, rate held fixed): floor 0 gives 0.27 at 0.064
and 0.05, 0.33 at 0.03, 1.00 only at rate 0; floor 0.5 gives 0.47 at rate 0. Rates under the lenders' lowest
are not rates anyone lends at, so the floor stays; its stated reason (dearth, dowry, old age) is unchanged and
nothing here supports a lower figure.

The wage still drifts (Rome, `ROME_SPIN_UP_YEARS=2,1`, labourer wage per hour, opening 1.0, game years 1 to 8,
spin-up cache bypassed for the "before" run): before 0.145, 0.129, 0.117, 0.113, 0.116, 0.136, 0.134, 0.119;
after 0.129, 0.106, 0.090, 0.078, 0.069, 0.062, 0.056, 0.050. The wage is a tenth of its opening figure by
year one in both, so the savings leak is not what drives it down; the remaining candidates are 473 (the wage
schedule against the households' outside option) and the wish itself (two years of surplus per household).
Small fixture, ten years, mean labourer wage: before 0.075 to 0.022, after 0.075 to 0.023; the rate path
falls to near zero in both.

Not merged: the opening rate search is on branch `fix-526-opening-rate`. It lifts the settled income by about
a third and then no further, and Rome's labourer wage over the first years is no better and drifts lower than
without it, so the savings wish is not what drives the wage collapse. Next to look at: the opening wage
(`wage_schedule`, anchored on the coin metal's table cost) against what labour earns at the households' own work
(473), and the size of the savings wish itself.

## Measured: the wealth households want against the wealth the opening holds

Rome without a spin-up (`build_setup(unopened_sim(civ="rome_100ad"))`, then `opening.open_economy`) settles at about a
quarter of the full-employment ceiling. Against total household income, the opening holds producer cash of about a
year, plant at replacement value of a few hundredths of a year and household cash of under a fifth of a year, while the
savings wish asks for roughly four years. A throwaway probe added firm equity of K years of income to the wealth
`goods_orders` sees, split by `ownership_share`: the settled ratio rose with K and reached the ceiling only near four
years. The opening's real firm equity (about a year) lifts it by about a third, as the rate search did.

So the leak closes only when households hold wealth near the wish, or the wish is smaller. Order of work:
1. Land and plot titles carry a value (538), the asset the earlier probe found missing.
2. A `view.equity(agent)` on the `MarketView` protocol (firm net worth and titles), read alike by `goods_orders` and
   `_opening_bids`, so year-0 income matches the opening.
3. Question the wish itself: two years of surplus income plus a cash buffer is a labelled figure; check it against
   sources on pre-modern household saving before building assets to match it.
4. Then 545 (own plots in the opening) can land, and `opening_income_per_head` can go. The wage drift is 473.
