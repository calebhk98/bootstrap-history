# A borrower that cannot pay interest compounds its debt without limit

**Status:** closed. A borrower past its credit ceiling draws nothing for interest; the unpaid interest is arrears, and arrears past `ARREARS_YEARS_BEFORE_DEFAULT` default the claim through the pool and close the firm (`sim/agents/borrowing.py`, `borrowing_arrears.py`). The founder's household keeps `enforce_credit_limit`, a separate rule on the same idea; unifying it is not done. Test: `sim/tests/test_bounded_firm_debt.py`.

Found closing 586. In the playtest save (Rome, seed 11, 221 AD) one firm holds a facility far above every other
actor's, with an empty purse: each year `Borrowing.pay_interest` (`sim/agents/borrowing.py`) draws the interest on
the facility and adds it to the debt, so the debt grows at the borrowing rate for ever and the pool's flows grow
with it. Nothing makes a firm whose debt exceeds its credit ceiling default or stop borrowing to pay interest.

Measure: load the save and print each borrower's `purses.debt` against its credit ceiling and purse.

What it would take: a borrower past its ceiling is refused the draw and closes (`write_off`) or its interest falls
into arrears; test that a firm with no income reaches default in bounded years.
