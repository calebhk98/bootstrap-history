# A state's reserve above a few years of need is debited to "discretionary" and leaves the economy

**Status:** open

The state budget sweeps any reserve above a few years of its standing need into an outlay named `discretionary` (`sim/engine/actors/government.py`, `self.debit(excess, "discretionary")`). The money is not paid to anyone, bought with, lent or saved: it leaves the simulated economy. It was added so that a hoarding state could ever run short and fire the need-driven levy (`Complaints/300`).

Why it matters: a sink with no recipient is the mirror image of money from nowhere. While state revenue is a share of society output rather than a stock of coin, nobody else loses income, so the practical effect is small today; but it hides what a real surplus does (works, gifts, lending, a treasure that someone could seize), and it removes the supply the loanable-funds market reads from the state's reserve (`Complaints/110`, `412`).

What it would take: once the capital market lands, let a reserve above need be lent through it (the state as a saver, earning interest), and spend the rest on named things the state can buy (works, the dole, a war chest that can be seized or spent); then delete the sweep. Measure with `python3 sim/budget_series.py <civilisation id> <years> <seed>`: the `discretionary` line should be zero. Related: `Complaints/300`, `448` (revenue is a fitted share), `110`, `412`.
