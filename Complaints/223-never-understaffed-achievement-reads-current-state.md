# The "no concern ever closed for want of staff" achievement is awarded after dozens of staffing closures

**Status:** open

At the end of the run `score` marked "no concern ever closed for want of staff" as achieved although the tester's
reports show closures of 10 to 95 concerns in many years.

Cause: `sim/engine/proto/score.py` (`_score_achievements`, `never_understaffed`) reads
`len(sim.shut_for_staff) == 0`. `shut_for_staff` (`sim/engine/core_properties.py`) is a view of `projects.closures` with reason
"staff", and `projects_staffing.py` deletes the record when the concern reopens. So the achievement means "nothing is shut for staff at
the moment you win", not "never". The function's own docstring says each achievement is "true of the WHOLE run".

What it would take: a saved counter (or a set of ids ever closed for staff) that is not deleted on reopening, and a test that closes and
reopens a concern and then expects the achievement to be lost. Other achievements the tester checked (`free_hands_only`, `clean_ledger`,
`corpus_intact`, `outpaced_the_fastest_plan`) read durable fields and looked right.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 212). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.
