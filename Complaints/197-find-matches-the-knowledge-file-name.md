# `available electricity` returns only "Signal flags": `find` matches the knowledge-file name

**Status:** open

`available electricity` returns exactly one item, Signal flags for maritime communication, and no electrical technology. The cause is in the data: `com_signal_flags` has `"kb": "50_electricity.md"` (`data/branches/24_comms_computing.json`), and the search matches the doc anchor, so the filing-cabinet name of the knowledge file becomes a player-visible "subject". The tester read this as the category system being untrustworthy.

Reproduces on the current branch:

    printf 'available electricity\nquit\n' | python3 sim/simulator.py play --civ england_1300 --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

What it would take: either do not match the `kb` path in player-facing search (the anchor exists so ids resolve, not as a subject), or file the node's `kb` under the document it belongs to; then a test that a search word only matches what a player can see (id, name, aliases, a real category). Related: 22 (closed; made `find` match the anchor), 196.

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.
