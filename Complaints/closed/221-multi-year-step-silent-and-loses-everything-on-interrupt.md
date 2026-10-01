# `step N` prints nothing until it finishes, and interrupting it loses every year already simulated

**Status:** closed

The tester ran `step 200` from 400 AD (a 1,860-person company): no output for about 51 minutes, then interrupted with Ctrl-C and the session
file still held year 400. A following single `step` took 20 seconds, so the batch may have needed about 68 minutes; the tester could not tell working from hung.

Code: `sim/engine/cli_interactive.py` saves once, after `_agent_dispatch` returns ("SAVE FIRST, THEN SPEAK"), and `_cmd_step`
(`sim/engine/proto/dispatch.py`) loops over the years inside the one dispatch with no progress line and no intermediate save. Killing the process
mid-loop therefore discards all simulated years. (The loop does stop early when a warning it issued comes true; that is unrelated.)

Not corruption: the save is intact at the old year. Severity is lost time and no feedback.

What it would take: print one line per simulated year (year, cash, completions, losses) as the loop runs; save every year or every few years inside
a multi-year step so an interrupt keeps completed years; optionally warn before a long step with an estimated duration.
Related: 181 (late-game step time, partly done). The tester also asked for a visible "advancing" indicator for single 10-20 second steps.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 210, 221, 222, 223). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.

**Resolved:** each simulated year of a multi-year step is saved as it ends (the play and agent loops set a hook in `sim/engine/proto/step_progress.py`) and a progress line per year goes to stderr, so an interrupt keeps every finished year. An estimated-duration warning before a long step was optional and is not built. Test: `sim/tests/test_step_interrupts_and_alerts.py`.
