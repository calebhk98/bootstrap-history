# Reaching the goal under fog does not end the run, the score total stays withheld, and there is no finish-and-score action

**Status:** open

The tester won (junction transistor, 399 AD) and `score` still printed "TOTAL: -- (not computable until the run ends under fog)"
with technology coverage withheld. Winning is deliberately not an ending (`sim/engine/proto/state.py`, `_agent_end_reason`: the run continues to the
horizon or the founder's death), and under fog the coverage share is only revealed once the run has ended. The only ways to end are to step to
the horizon (hundreds of simulated years, see complaint 225) or die. `quit` ends a session, not a run; `withdraw` is political.

Why it matters: a player who has just won cannot see what they scored, which is the obvious thing to want at that moment.

What it would take: an explicit "finish this run and score it" action that ends the run (the save stays loadable for optional continuation), or a
provisional total with a range that does not reveal undiscovered nodes; say on the victory screen how the score becomes available.
Closed 183 made `score` show totals for a missed goal; this is the won-goal, fog case.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 211, 220). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.
