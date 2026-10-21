# A debt far past its credit ceiling never defaults when interest is nil

**Status:** closed - a debt over its ceiling owes the excess as principal due and unpaid excess counts as arrears at any rate (`Borrower.settle_interest`); `sim/tests/test_one_default_rule.py`.

Found rewriting `insolvency_whole_game` (640). The default rule (`Borrower.settle_interest`, `sim/agents/borrowing.py`;
`borrowing_arrears.in_default`) counts arrears only from unpaid interest. When the market rate is nil, no interest is
due, so a borrower at many times its ceiling builds no arrears and is never defaulted; in the old whole-game run a
founder's debt sat at tens of times its limit for years. 641 puts a floor under the lenders' ask, which makes nil rare,
but the rule should not depend on it: a debt over its ceiling is a breach whatever the rate.

What it would take: a borrower whose debt exceeds its ceiling owes the excess as principal due (a margin call), and
that unpaid excess counts as arrears like unpaid interest. Test: call the settlement with a built borrower over its
ceiling at a rate of zero; it enters arrears and defaults after the arrears years.
