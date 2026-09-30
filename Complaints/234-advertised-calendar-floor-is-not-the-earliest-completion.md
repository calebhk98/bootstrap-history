# The calendar floor `why` and `start` advertise is shorter than the payment schedule that actually binds, so the quoted finish year is wrong

**Status:** open

`start` and `why` print "calendar floor" and "expected calendar years with retries", both shortened by reputation. The money is paid in annual instalments of the bill divided by the nominal,
unshortened years (`sim/engine/core_step_phases.py`, `frac = min(1.0, 1.0 / max(1.0, node["yrs"]))`), so reputation never shortens the real schedule.
Measured (Han, corpus_written, same bill, capital unlimited):

    reputation 5   advertised floor 9.47   actual steps to finish 10
    reputation 70  advertised floor 5.62   actual steps to finish 10

The tester reports the same at every scale: the grid 12.2 adjusted years against 25 real; high-pressure steam 5.9 against 12; dynamo 3.5 against 7; vacuum tube 3.8 against 8; corpus dispersal 4.7 (nominal 8) still
owing seven years after one; zone refining 2.9 shown, six annual payments; 15.9 years of "remaining calendar" for a retry that completed in four. Once started the screens say it correctly ("about 2 more payment years"),
but the decision was made on the first number. Closed complaint 8 (expected below the floor) and 158 did other halves.

What it would take: show the earliest completion as the maximum of hours, calendar floor and payment schedule, in years and as a calendar year, and label the floor as a minimum; use the same figure in `state` and `portfolio`;
keep retries as a separate uncertainty. If the payment pace is meant to be shortened by reputation, use the adjusted floor in `frac`. A test comparing the printed expectation with a stepped completion would hold it.
Related: 240 (whole years burned by tiny remainders).

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 41, 44, 58, 71, 95, 99, 100, 116, 129, 140, 158, 173, 187, 202, 204). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.
