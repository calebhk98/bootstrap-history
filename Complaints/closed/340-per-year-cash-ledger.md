# A per-year cash ledger is missing

**Status:** closed - every change to the founder's cash goes through HouseholdState.credit/debit/reset_cash into the cash book (sim/engine/cash_book.py), the `cash` figure reads its causes from it and `money` shows the year by cause

`figures cash` itemises cash change from standing revenue, upkeep, living cost, mine cost and last year's project payments, and shows everything else as one 'not itemised' line. A player cannot reconcile a year: opening cash, each command payment, receipts, wages and advances, interest, refunds, hazards, closing cash.

## What would resolve it

Record each cash movement by cause as it happens in the engine (a ledger written where capital changes) and read it from the `cash` figure. Reported in Complaint 97.
