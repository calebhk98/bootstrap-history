# Resilience projects give no "before and after" hazard estimate before the money is spent

**Status:** open

Silage and the silo cost about 76 thousand pence, and the tester learned only afterwards that they lowered the Great Famine staff-loss estimate from about 12 to 11 percent. They liked the modest effect but wanted the number before paying: "at current conditions this would reduce expected famine staff loss from ~12% to ~11%", without revealing hidden tree information.

Untested on the current branch: the `why` screen read for this triage (cost, staff, failure risk, market line) showed no hazard-effect line, but `why` was not run on a mitigation node during a live hazard window. Check in a non-fog game with `why` on a node listed in the `HAZARD_COUNTERS` table for a hazard that `risk` shows.

What it would take: on `why`, for a node that counters a hazard now on `risk`, one line giving the estimate with and without it, computed from the same `hazard_relief` multiplier. Related: 124 (no lever on failure risk), 94, 202.

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.
