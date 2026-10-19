# A borrower that cannot pay interest compounds its debt without limit

**Status:** open

Found closing 586. In the playtest save (Rome, seed 11, 221 AD) one firm holds a facility far above every other
actor's, with an empty purse: each year `Borrowing.pay_interest` (`sim/agents/borrowing.py`) draws the interest on
the facility and adds it to the debt, so the debt grows at the borrowing rate for ever and the pool's flows grow
with it. Nothing makes a firm whose debt exceeds its credit ceiling default or stop borrowing to pay interest.

Measure: load the save and print each borrower's `purses.debt` against its credit ceiling and purse.

What it would take: a borrower past its ceiling is refused the draw and closes (`write_off`) or its interest falls
into arrears; test that a firm with no income reaches default in bounded years.
