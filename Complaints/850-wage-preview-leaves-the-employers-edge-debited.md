# The wage-work preview puts the purse back but not the employers' edge account

**Status:** open - read from the code, not reproduced

`Labour.work_for_wages_dry_run` (`sim/labour/labour_wage_ledger.py`) runs the sale and then restores the acting seat's purse (now by the
ledger's `RestorePurse`), the wage hour and income books, `wages_earned` and the log. The sale itself posts
`ReceiveFromEdge(EDGE_EMPLOYERS, pay, "wages for your own work")` (`sim/labour/labour_wages.py`, `work_for_wages`), which the ledger applies as a
transfer from the employers' edge account to the household (`Ledger.receive_from_edge`). Only the household side is put back, so each preview
leaves the employers' edge account lower by the pay it quoted (and whatever else the transfer records in the purses' book). The preview is the
`work ... preview` command and the wage fallback's quote, so it runs often.

Why it matters: money is created from the edge on every preview, and a quote is not meant to change any book. The fix is a pure quote of the
sale (the pay and the message from the rule, no posting), which retires the `work_for_wages_dry_run` view and `RestorePurse`.

The workforce-boundaries move kept this behaviour exactly (the equivalence check is the proof).
