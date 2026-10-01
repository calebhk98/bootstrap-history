# Completing the corpus says "closed / not in effect until open", yet `risk` and `state` already count it as a hedge

**Status:** closed

On completion the log says the written corpus is "STATUS: CLOSED / NOT OPERATING ... Not in effect until open: Standing". At the next checkpoint, before opening it, `state` and `risk` already credit it as a knowledge hedge (sack-loss chance from 80 to 45 percent, fraction lost from 40 to 22 percent).

This is the designed behaviour, not a state bug: `corpus_hedge()` in `sim/engine/core.py` uses `has` (finished copies exist and survive a closure) deliberately, and the completion message takes its text from the node's `lost_benefit`, which for `corpus_written` is only "Standing". But the two messages read as a contradiction: the completion text says what opening adds, not that the hedge is already permanent, so the player cannot tell which screen is right.

Verified by reading the code (`sim/engine/projects_completion.py` near the "CLOSED / NOT OPERATING" message, `sim/engine/core.py` `corpus_hedge`, `data/branches/00_core.json` `corpus_written`); not replayed, since it needs the corpus finished.

What it would take: the completion message lists both groups (in force from completion: the knowledge hedge; needs opening: standing, and so on) using the permanent-versus-while-open split that closed complaint 04 introduced, and a test that the wording and `risk` agree. Related: 04 and 53 (closed).

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.
