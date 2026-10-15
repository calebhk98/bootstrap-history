# The founder's job does not cover living costs, so a ruined founder cannot climb back

**Status:** open

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
