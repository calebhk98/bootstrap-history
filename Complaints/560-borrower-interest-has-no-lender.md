# Interest a firm, the founder or the state pays on its debt goes to no one

**Status:** open

`Borrower.pay_interest` (`sim/engine/actors/borrowing.py`) debits the interest to an outlay named `interest` and the founder's debt service is a deduction from the founder's money; neither is credited to a lender. Lenders (households, firms, the founder, the state) are a pool on the loanable market (`sim/engine/economy_capital_market.py`), so what a borrower pays is money leaving the modelled economy, the same shape as the old `discretionary` sweep (Complaint 499). The state's `interest_on_lending` income is the one place a lender is credited, and it is paid by the pool's borrowers in aggregate (including the unmodelled background borrowers) without debiting any named actor, so the two do not balance.

What it would take: split each year's interest paid across the funds' sources by their share of the pool and credit it to the source actors (households stay unmodelled and absorb their share), so modelled money is conserved. Measure with a run's `outlays["interest"]` against the lenders' income lines (no command sums them; a test would). Related: `110`, `412`, `499`.
