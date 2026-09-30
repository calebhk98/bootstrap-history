# Standing `allocate` orders go stale and nag "DIRECTED HOURS UNUSED" every year

**Status:** open

When a project's annual pace drops (less left to do, a calendar floor, a material shortage) an old fixed allocation keeps producing "DIRECTED HOURS UNUSED: you allocated hours to X this year that it could not use" year after year. The tester asked for either an automatic release of hours a project cannot use, or a clearer one-time reminder to clear completed or over-allocated standing orders.

Not replayed (needs a standing allocation exceeding a project's pace). The message is built in `sim/engine/core_step_phases.py` ("DIRECTED HOURS UNUSED: you allocated hours"); tests in `sim/tests/test_allocate.py`. What it would take: an option (per order, or a policy) that lowers the order to what was used; otherwise emit the message once per order until it changes and fold repeats into the yearly problems block. Related: 79 (persistent conditions), 101, 205.

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.
