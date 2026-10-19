# An active game slows to a stall in lender postings

**Status:** closed

Found by an agent playtest played legitimately (`Complaints/reports/playtest-rome-seed11-agent-legitimate-log.md`,
Rome, seed 11, branch `pm-complaints-burndown` at `fb462538`). With about thirty concerns running and loans taken,
a game year took about twelve seconds early on, then grew year by year until a single year did not finish in over
half an hour at 143 AD. The save file grew from tens of megabytes to well over that. Interpreter dumps during the
slow year sat in `firm.act` → `pay_interest` → `note_lender_posting` (`sim/engine/economy_interest.py`).

Reproduce: the save at 143 AD is kept outside the repository by the session that found it (ask for it, or replay
the log's commands); `echo "step 1" | python3 sim/simulator.py play --session SAVE`.

Why it matters: the release criterion is that an agent plays the whole game; an active game cannot get past the
middle of the second century. A cost that grows with the number of postings or contracts per year is the likely
shape (a list scanned per posting, a ledger or contract registry that is never pruned, or a save that keeps every
posting).

What it would take: profile one slow year from the save, find what grows, make it linear in the year's activity
(and prune what the game no longer needs to keep), and add a test that the cost of a year does not grow with the
number of past years' postings.

## Resolution

Cause, measured on the 143 AD save: every firm held a facility claim on every other firm (a draw was split over
all lenders by offer), so claims grew with the square of the firms (about 176 thousand rows, 60 MB of the
save, almost all of them firm-to-firm dust). Worse, `Purses.pay_interest` and `payroll.share_out` paid many
payees one by one, and a payer with an empty purse drew its whole facility again for each payment, each draw
posting to every lender, and each interest part received by a lender that was itself a borrower repaid all of
that lender's claims. About three million lender postings in 120 seconds.

Fix: a batch of payments covers the payer's shortfall once (`Purses.cover`, `ledger.cover`); a lender offering
under a small share of the funds on offer takes no part in a draw (`LENDER_MATERIALITY`, a labelled stand-in,
retired by Complaint 580); rounding-residue repayments and rows are not posted or kept. Regression test:
`sim/tests/test_borrower_draws_once_per_batch.py` counts draws, not seconds.

One year from the save (`step 1`, 143 AD) used to take over thirty minutes and now completes in about three and
a half minutes, load and save included.
