# Spending can run past the credit limit when upkeep of built works nears revenue

**Status:** open

The slow check "debt stays inside a credit limit" (`sim/tests/test_early_playtest.py`,
`python3 -m sim.tests --only early_playtest --slow`) fails on the labour-market-core branch: worst capital
-23.7 million. It passes on main (`bcd8b65`). The cause is not in the labour code.

The check's game is Rome with automation on, a rich start and 400 slaves. On the branch, auto-hire's
affordability is measured against what hiring costs (Complaint 396), so the household's staff grows past
1,000 where main's stayed under about 60. The household then builds far more.

First breach, measured with a scratch script that steps the check's game and stops at the first year with
`capital < -credit_limit()`:

| | Year 188 |
|---|---|
| capital | -21.45 million |
| credit limit | 20.48 million |
| revenue | 27.3 million a year |
| upkeep of built works | 20.2 million |
| living cost | 1.86 million |
| wages | 0.02 million |
| staff | 817 |

The overshoot is about 5% in that year, and debt reaches about 16% past the limit later. Payroll is a
rounding error here, so the spending that crosses the limit is project spending or upkeep.

Why it matters: the credit limit is meant to be a wall. A household that grows large enough to carry upkeep
close to its revenue walks through it, and any actor that grows (firms, players) will do the same.

What it would take: find which outflow is charged without checking the room left under the limit, in
`sim/engine/step_phase_*` and the projects code: project starts, upkeep of works that cannot be closed, or
founder-hour arrears. Either refuse it or close works to stay inside the limit, as the payroll shedding
already does for staff (`step_phase_staff.py`).
