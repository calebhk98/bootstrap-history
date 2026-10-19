# The lending pool grows to an absurd balance

**Status:** closed

Found closing 582. In the agent playtest (`Complaints/reports/playtest-rome-seed11-agent-to-221.md`, Rome, seed 11, around 160 to 221 AD) the pooled lender
`pool:credit` (Complaint 580) held a balance many orders of magnitude above the economy's money stock. Something
keeps putting money into the pool without taking it out: savers' top-ups that are never repaid, deposits counted
twice, or interest credited to the pool and also to depositors.

Measure: load the playtest save at 221 AD and read the book's balance for `pool:credit` against the total money held
by households and firms (no committed command prints both).

What it would take: trace every edge into and out of the pool over a few years, find the one that does not balance,
fix it, and add a test that the pool's balance stays within the deposits it holds plus the year's interest, over
several stepped years.

## Resolution

Cause: the pool lent out the interest it had received and owed its depositors. `Purses._fund_pool` topped the pool up
from the savers only when its cash fell short of the draw, so a draw spent the pending interest; at settlement the pool
could not pay it and the unpaid share was dropped, leaving loans out with no deposit behind them (loans above deposits
by the interest owed and never paid). Every year this repeated.

Fix: a draw or a deposit taken back leaves the pending interest in the pool (`_fund_pool` counts only cash beyond it),
so the savers top up instead and settlement pays in full. The pool holds deposits less loans out plus the interest
pending, and after settlement deposits less loans out; the savers top-up is repaid from excess at settlement.

Regression tests: `sim/tests/test_pool_balance_matches_its_books.py`.

What remains: the playtest save balance came mostly from one insolvent firm whose interest is added to its debt
every year with no default, so its debt compounds without limit (Complaint 588).
