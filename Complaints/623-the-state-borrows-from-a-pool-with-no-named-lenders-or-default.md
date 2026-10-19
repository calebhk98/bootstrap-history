# The state borrows from the pool: no named creditors, no repayment in land and no default

**Status:** open

Part of Complaint 542 (State capacity and tax rates are typed, there is no corvée, and the fiscal crisis is a fixed cascade).

Depends on 538 for repayment in land.

**What is wrong.** Borrowing is from the general loanable pool once a technology allows it. There are no named lenders, no repayment in land and no default.

**Evidence.** `sim/agents/government.py`, `borrowing.py`.

**Why it matters.** Rome in the Second Punic War borrowed from citizens and repaid part in public land.

**What it would take.** Named state creditors (citizens, contractors, temples), repayment in land once titles exist, and default.

**Test.** A test: a state that cannot pay defaults and the creditor's book shows the loss; repayment in land transfers a title.
