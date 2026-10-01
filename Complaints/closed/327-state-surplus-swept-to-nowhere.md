# A state's reserve above a few years of need is debited to "discretionary" and leaves the economy

**Status:** closed - pinned by sim/tests/test_state_surplus.py

The state budget sweeps any reserve above a few years of its standing need into an outlay named `discretionary` (`sim/engine/actors/government.py`, `self.debit(excess, "discretionary")`). The money is not paid to anyone, bought with, lent or saved: it leaves the simulated economy. It was added so that a hoarding state could ever run short and fire the need-driven levy (`Complaints/286`).

Why it matters: a sink with no recipient is the mirror image of money from nowhere. While state revenue is a share of society output rather than a stock of coin, nobody else loses income, so the practical effect is small today; but it hides what a real surplus does (works, gifts, lending, a treasure that someone could seize), and it removes the supply the loanable-funds market reads from the state's reserve (`Complaints/106`, `307`).

What it would take: once the capital market lands, let a reserve above need be lent through it (the state as a saver, earning interest), and spend the rest on named things the state can buy (works, the dole, a war chest that can be seized or spent); then delete the sweep. Measure with `python3 sim/budget_series.py <civilisation id> <years> <seed>`: the `discretionary` line should be zero. Related: `Complaints/286`, `315` (revenue is a fitted share), `106`, `307`.

Done: the sweep is deleted (`sim/engine/actors/government_surplus.py`). The reserve above `RESERVE_CEILING_YEARS_OF_NEED` years of need hires labourers for works (a line the labour market feels); the reserve held against risk is supply on the loanable market and is paid its share of borrowers' interest as `interest_on_lending`. A war chest and the dole beyond the standing line are not added; the works labour is capped by `MAX_WORKS_SHARE_OF_WORKING_AGE`. The interest the state earns is its share of what borrowers paid (Complaint 332).
