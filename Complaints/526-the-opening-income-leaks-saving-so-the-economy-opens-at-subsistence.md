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
