# The state borrows from the pool: no named creditors, no repayment in land and no default

**Status:** closed. A state is a borrower that names its lenders: `Purses.named_lenders` (`sim/agents/named_lenders.py`) attributes each draw on its facility to the pool's depositors (households' savings, firms, merchants, other states) in proportion to what each placed, and `Government.creditors()` reads the claims. Arrears and default run the shared 589 rule (`Borrower.settle_interest`); a default writes down the named lenders' deposits by their claims (a lender that came after the loan loses nothing) and the loss goes on the state's record, which adds `DEFAULT_RECORD_PREMIUM` to the rate it pays until it fades (`sim/agents/government_credit.py`, `borrowing_arrears.py`). Repayment in land is not done: it waits on titles (538). Test: `sim/tests/test_state_named_lenders.py`.

Part of Complaint 542 (State capacity and tax rates are typed, there is no corvée, and the fiscal crisis is a fixed cascade).

Depends on 538 for repayment in land.

**What is wrong.** Borrowing is from the general loanable pool once a technology allows it. There are no named lenders, no repayment in land and no default.

**Evidence.** `sim/agents/government.py`, `borrowing.py`.

**Why it matters.** Rome in the Second Punic War borrowed from citizens and repaid part in public land.

**What it would take.** Named state creditors (citizens, contractors, temples), repayment in land once titles exist, and default.

**Test.** A test: a state that cannot pay defaults and the creditor's book shows the loss; repayment in land transfers a title.
