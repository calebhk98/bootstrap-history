# The founder and other borrowers default by two rules

**Status:** closed. The founder's household is a borrower like any other: `Household` (`sim/agents/household_borrowing.py`) runs `Borrower.settle_interest` with its own ceiling and rate. Interest is drawn within the ceiling, the rest is arrears, and `ARREARS_YEARS_BEFORE_DEFAULT` years of arrears default the debt. `enforce_credit_limit` is now only the founder's responses past the ceiling (stop projects, mothball, seize, disperse); the default (`default_on_debt`) enters bondage or settles. Test: `sim/tests/test_one_default_rule.py`.

Found closing 588. Firms and traders now pay interest only within their credit ceiling, carry the rest as arrears
and default after a bounded run of years in arrears (`sim/agents/borrowing.py`, `borrowing_arrears.py`). The founder's
household still follows its own rule (`enforce_credit_limit`, `sim/engine/economy_credit.py`: halt work, shed,
settle once a decade). Two rules for one thing (CLAUDE.md "general actors"; the project's duplication pattern).

What it would take: one arrears-and-default rule in `sim/agents/` that every borrower, the founder's household
included, runs through, with the founder's choices (stop a project, mothball) as the actor's own responses before
default; the founder-specific settlement folded into it. Test: the same debt, income and ceiling give the same
outcome year by year for the founder and a firm.
