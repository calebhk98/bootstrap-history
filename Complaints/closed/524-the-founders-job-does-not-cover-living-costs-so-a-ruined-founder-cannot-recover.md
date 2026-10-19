# The founder's job does not cover living costs, so a ruined founder cannot climb back

**Status:** closed - a household lives within its income whether or not it holds savings, so the default founder's wage carries them

Since Complaint 518 the founder's whole standing income is the one `_wages_for_your_own_work` line (the unspoken-for
hours sold in the held trade at the market wage). In a Rome game whose concerns are shut or never opened that income is
below `living_cost()` every year, so net money is negative for as long as nothing else earns. 518's resolution says as
much ("The Rome founder's income no longer covers living costs; the opening's wages are the 507 Stage 2 work").

Measured on the scenario `sim/tests/test_insolvency_whole_game.py` builds (a founder pushed to three times the credit
limit, then five full years; there is no command, run its `_ruined_founder_run`): after the settlement the revenue
line is the wage alone, living cost sits above it every year, the gap does not close, the credit line shrinks with the
income it is priced on, and the debt grows past the limit again within two years. No second settlement comes inside the
once-a-decade rule (`SETTLEMENT_MIN_INTERVAL_YEARS`), so debt over the limit persists.

Checks that fail because of it (not weakened, left red until the income side changes):

- `insolvency_whole_game`: "a ruined founder rebuilds rather than freezing" and "a ruined founder's debt stays inside
  the credit limit once the settlement has run".

A check that only needed the founder not to settle in its first year was moved off the edge (`interface_honesty`, "a
multi-year step stops the moment it is CLOSE TO THE LIMIT too": it starts nearer the 70% line, because interest on an
overdrawn purse plus the yearly deficit crossed the limit within one step, so the step settled instead of warning).

What it would take: the opening's wages (507 Stage 2) so a held trade pays at least what the founder lives on, or a
reason a ruined founder sheds living cost faster (`living_cost` carries a household base that does not fall with
income). Re-measure both checks after 507 Stage 2 before changing either.

## Partial fix

A household in arrears no longer pays for dependants its income cannot carry (`dependants_beyond_means`, charged in
`_step_money_seat`): after upkeep, the rest of the living cost and interest, only the share of the surplus the
creditors do not take (`DEBT_SERVICE_SHARE_OF_SURPLUS`) keeps dependants. Debt stays inside the limit and cash rises
in `python3 -m sim.tests --slow --only insolvency_whole_game`. What remains is the opening's wages (507 Stage 2): the
standing job still pays less than `living_cost()` reports, and that figure (and the credit floor priced on it) still
counts the full dependants.

## Resolution

Measured on the default Rome game (`sim(manual=False)` in `sim/tests/test_founder_income_living_cost.py`): the founder sells
the idle hours in the held trade at the market wage (the "going into nothing" line on the state screen is about
projects only; the wage line already sold them). That wage covers one person's subsistence, but not the household
base on top of it. The agent economy's own per-person need floors (`agent_need_floor_costs`) sit far below the
subsistence heuristic, so a society household of the same income does not pay a fixed household base either: it pays
what its income carries.

`dependants_beyond_means` (`sim/engine/economy_debt_service.py`) now applies to a household with savings as well as to one
in arrears: dependants are kept out of the income surplus (the creditors' share only when in arrears), and savings are
not spent on them. `recurring_living_cost` is the figure the recurring net, the sustainable debt and the insolvency
counter now read, so they agree with what the money phase charges. Subsistence itself is never shed. Tests: the new
topic `founder_income_living_cost` and the updated `ruined_household_dependants`; `insolvency_whole_game` passes.
