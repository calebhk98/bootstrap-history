# The lending pool pays deposit interest it does not hold

**Status:** open

Found by an agent playtest (`Complaints/reports/playtest-rome-seed11-agent-to-221.md`, Rome, seed 11, from about 158 AD). A step failed with `internal error handling that
command: InsufficientFunds: pool:credit holds ... engine_coin but must pay ... (interest on deposit)`; from about
164 AD every step failed once and the retry worked. The pool (Complaint 580, `sim/agents/purses.py`) settles
depositors' interest from what it holds; when borrowers' interest has not come in, or defaults have eaten it, the
pool cannot pay and the year aborts partway, which also leaves the retry stepping a half-run year.

What it would take: the pool pays depositors out of the interest it actually received that year (pro rata, so the
deposit rate is an outcome), never more; a shortfall is a loss to depositors booked once, as defaults already are.
Test: a year in which borrowers pay less interest than the deposit rate implies settles without error and pays
depositors exactly what came in. Also check that a step that raises partway does not leave a half-run year.
