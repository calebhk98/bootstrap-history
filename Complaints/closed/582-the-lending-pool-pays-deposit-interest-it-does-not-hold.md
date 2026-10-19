# The lending pool pays deposit interest it does not hold

**Status:** closed

Found by an agent playtest (`Complaints/reports/playtest-rome-seed11-agent-to-221.md`, Rome, seed 11, from about 158 AD). A step failed with `internal error handling that
command: InsufficientFunds: pool:credit holds ... engine_coin but must pay ... (interest on deposit)`; from about
164 AD every step failed once and the retry worked. The pool (Complaint 580, `sim/agents/purses.py`) settles
depositors' interest from what it holds; when borrowers' interest has not come in, or defaults have eaten it, the
pool cannot pay and the year aborts partway, which also leaves the retry stepping a half-run year.

What it would take: the pool pays depositors out of the interest it actually received that year (pro rata, so the
deposit rate is an outcome), never more; a shortfall is a loss to depositors booked once, as defaults already are.
Test: a year in which borrowers pay less interest than the deposit rate implies settles without error and pays
depositors exactly what came in. Also check that a step that raises partway does not leave a half-run year.

## Resolution

Cause: `Purses.settle_interest` (`sim/agents/purses.py`) fixed the total of deposits first, then topped the pool up
with a deposit from the savers, which raised the savers principal; the shares were then taken from the grown
deposits over the old total, so the payments summed to more than the pool held and the book refused the last one.
It happened whenever lenders had taken deposits back (or the pool was otherwise short) between the interest coming
in and the settlement. The pending interest had already been reset, so a retry paid nothing and succeeded.

Fix: settlement takes its shares from the deposits as they stand, pays at most the interest received and never
more than the pool holds, and no longer tops the pool up. The deposit rate is whatever that comes to; interest
lost in a default is simply not paid, and a default loss of principal is still booked once by `write_off`.
The failure is made impossible; the year is not made atomic. A step that raises partway still leaves the
phases before the failure run and the year counter not advanced (the agent protocol saves after a failed
command), which is why the retry stepped a half-run year.

Regression tests: `sim/tests/test_pool_pays_what_it_received.py`.
