# Top-level `help` mentions pasteable JSON commands to a non-technical player

**Status:** closed

The "how to send a command" section of `help` ends "Pasting a JSON command works too, if you happen to have one", and the following paragraph is about scripts and agents (one command per invocation). The tester (a first-time player) called this technical noise in an otherwise clear help screen. Closed complaint 172 made `--help` player-facing; the in-game `help` first screen still carries agent-protocol text.

Reproduces on the current branch:

    printf 'help\nquit\n' | python3 sim/simulator.py play --civ england_1300 --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

What it would take: move the JSON and one-command-per-invocation notes to `help sittings` (which exists) or a developer topic, keeping the first `help` to the command loop. Related: 172, 177 (closed).

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.
