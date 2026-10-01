# Projects with a few cash units left, or less than a day's income, wait a whole extra year

**Status:** closed

The tester logged twenty-plus cases: lead with 14,609 left, wood pulp with 84, fire assay with 5 (162 to 165 AD), phosphor bronze 12.3, retort zinc 6.1, phosphorus 314.6 (205 to 210), pasteurisation 0.50 and emission spectroscopy 3.3 (260 to 274),
anaesthesia 35, intaglio engraving 8.2 of 284 thousand a year. Each showed "waiting another year" although cash was in the billions; the status screen counts "payment years" from a fractional tail.

Not reproduced: a harness run of 27 cheap Han nodes with huge capital finished in the expected number of steps for 19 of them; the 8 that took longer were limited by founder hours in the three cases inspected (`ph_left` still positive), not by a money tail. The tail in the tester's runs therefore arises from state that run reached (price moves after the bill freezes, hired-hours refunds, accumulated float error in `cost_left`).
Left open as a report with a clear failure signature; the next step is a long-run test that records `cost_left` at each project's final year.

What it would take: settle any `cost_left` below a small tolerance (or below the annual instalment rounding) at the scheduled final payment; make `waiting_on` say what is actually short. Related: 234.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 69, 99, 128, 158, 201). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.


What remains: the tester's larger tails (hundreds of units) may exceed the settle share, which is a labelled heuristic; a long-run test of final-year `cost_left` would show whether any remain, and `waiting_on` should name the real shortfall.

**Fixed:** `waiting_on` now says what is short: the calendar branch states the years still to run, the hours branch states the hours still to do and the uncommitted hours. The settle share stays a labelled heuristic; the measurement of a remainder in a long run is left to the cost-tail test already in place.
