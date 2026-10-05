# The state's reserve dominates the loanable pool

**Status:** closed - does not apply to the agent economy: the state offers no funds

This was written against the old engine market, where `LENDABLE_RESERVE_SHARE` of the state's reserve counted as supply and pulled the market rate down. The agent economy does not have that path. The only producer of a `FundsOffer` is `sim/economy/households_orders.py` (a cohort's cash beyond its bids and target); `year_goods.py` collects offers from cohorts only, and `state_finance.py` only queues a `LoanRequest` for a deficit. Measured on the fixture (`run(small_setup(), 30)`, spying `Economy._lend`): the state's offers are none; cohort offers split about four fifths from the town, one seventh from the farms and the rest from the hills, with the richest cohort in each tile the largest part.

What the agent economy does instead: the state's purse is idle cash in `accounts.Book` and is neither lent nor counted in the pool; the state borrows from households up to a debt limit. A state that lends its surplus would be a bank-like actor; that belongs to Complaint 106 (`Complaints/reports/agent-economy-capital-markets.md`).

Related: 106, 308, 332.
