# Request: a replay option that remembers which technologies you built in an earlier run, with fog lifted only for those

**Status:** partly - after a run ends, `again` (play) starts a new game with the ids you built revealed, and `play`/`agent --known-routes <file>` does the same from the `<session>.routes.json` written at the end (`sim/ui/replay.py`, test `sim/tests/test_replay_known_routes.py`); remains: no end-to-end test drives a run to its end and through `again`

C: fog resets between runs; for a mortal scenario meant to be replayed, a "lessons" carry-over after a death (a new run that remembers which nodes you built before, fog lifted only for them) would make replays less of a re-discovery grind. Not a defect; fog staying serious was praised by both Rome testers ("please retain fog").

What it would take: an option on the death or end screen to start a new game with a list of "known routes" (ids the player built, hidden from the fog redaction); the save must still be a single run (4.6). Related: 70, 98.


Found in the final blind playtests of this branch (three mortal fog Mexica 1500 runs; C design complaints and suggestion 8). Reports: `Complaints/reports/playtest-mexica-1500-mortal-three-runs.md`; triage: `Complaints/reports/final-playtests-triage.md`.
