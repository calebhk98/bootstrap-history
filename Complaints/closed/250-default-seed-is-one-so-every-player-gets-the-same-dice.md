# Every game uses seed 1 unless told otherwise, so every player gets the same founder lifespan, the same invasion and plague rolls and the same early failures

**Status:** closed

All three Mexica runs lost the founder in 1538 at "about 73", all three were sacked in all three invasion years, and one tester's `patron_local` failed three times running (risks 15%, 11%, 8%, about 1 in 750). These are one random stream, not fate.

Cause: `play --seed` defaults to 1 (`sim/engine/cli.py`, `--seed ... default=1`), and the new-game menu hard-codes `args.seed = 1` (`sim/engine/cli_interactive.py`, two places). The README says only "`--seed` fixes the dice, so a game can be replayed", not that the default is a fixed seed. Measured with the harness (`S.Sim(... random.Random(seed), cfg={"immortal": False})`, Mexica): remaining lifespan for seed 1 is 37.3 years (death in 1538, displayed age 35 + 38 = 73), for seeds 2 to 6 it is 45.7, 28.8, 28.3, 18.6 and 32.0. The first `random()` of seed 1 is 0.134, under the 15% `patron_local` risk, so any test that draws early fails the same way. Reproduced: a mortal, fog Mexica `play --seed 1` run stepped with bare `step` dies in 1538 with "THE FOUNDER DIES, aged about 73".

Why it matters: a player who expects variation (and a reviewer comparing runs) is seeing one fixed ensemble member: the "predetermined invasion", "fixed timer" and "bad luck" readings in the reports are the same artefact. It also defeats the ensemble validation CLAUDE.md 4.2 describes for anyone playing by hand.

What it would take: draw a fresh seed per new game (print it on the start screen and save it, so a game is still replayable with `--seed N`), keep `--seed` explicit for tests; say so in the README. Related: 251, 27 closed.


Found in the final blind playtests of this branch (three mortal fog Mexica 1500 runs; C bug 5 and design complaints; tester could not know the stream was fixed). Reports: `Complaints/reports/playtest-mexica-1500-mortal-three-runs.md`; triage: `Complaints/reports/final-playtests-triage.md`.
