# An active game slows to a stall in lender postings

**Status:** open

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
