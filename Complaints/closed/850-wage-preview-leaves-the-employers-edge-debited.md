# The wage-work preview puts the purse back but not the employers' edge account

**Status:** closed - the wage preview is a quote: `work_for_wages(trade, hours, commit=False)` (`sim/labour/labour_wages.py`) posts nothing, logs nothing and keeps no book (the hours count against the year only while the loss note is worked out), so the employers' edge, the purse and the cash book are untouched; `work_for_wages_dry_run` is that call and the workforce no longer sends `RestorePurse` or `DiscardEventsAfter`. Tests: `sim/tests/test_household_labour_rules.py` (`SellingHours`), `sim/tests/test_wage_work_books.py` (`DryRun`).

`Labour.work_for_wages_dry_run` (`sim/labour/labour_wage_ledger.py`) runs the sale and then restores the acting seat's purse (now by the
ledger's `RestorePurse`), the wage hour and income books, `wages_earned` and the log. The sale itself posts
`ReceiveFromEdge(EDGE_EMPLOYERS, pay, "wages for your own work")` (`sim/labour/labour_wages.py`, `work_for_wages`), which the ledger applies as a
transfer from the employers' edge account to the household (`Ledger.receive_from_edge`). Only the household side is put back, so each preview
leaves the employers' edge account lower by the pay it quoted (and whatever else the transfer records in the purses' book). The preview is the
`work ... preview` command and the wage fallback's quote, so it runs often.

Why it matters: money is created from the edge on every preview, and a quote is not meant to change any book. The fix is a pure quote of the
sale (the pay and the message from the rule, no posting), which retires the `work_for_wages_dry_run` view and `RestorePurse`.

The workforce-boundaries move kept this behaviour exactly (the equivalence check is the proof).
