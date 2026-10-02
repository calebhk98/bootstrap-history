# `stuck` names a concern as the best one to open that `open` then refuses for want of a specialist foreman

**Status:** closed

After building Toys and dolls with no carpenter on the payroll, `stuck` says "The best you could actually open
right now is hom_toys_dolls, which would earn 281,451 a year against 3,753 of upkeep: 'open hom_toys_dolls'".
`open hom_toys_dolls` answers "REFUSED: no qualified foreman is free: this concern needs 0.25 carpenter FTE".

    printf 'start hom_toys_dolls\nstep\nstuck\nopen hom_toys_dolls\nquit\n' | python3 sim/simulator.py play --civ han_china_100ad --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

Cause: `sim/ui/proto/dispatch_inspection.py` (`_openable`, around line 392) tests free scholars, free craftsmen
and the opening fee, but not the specialist foreman that `open` enforces (closed 149 put the foreman on `why`;
`state` already says "missing 0.25 carpenter ('hire carpenter 1')" for the same concern).

What it would take: make the recommendation call the same feasibility check `open` uses, or say "openable once
you hire a carpenter"; include the wage or advance in the quoted net. Complaint 127 (closed) did the start-time
half; this is the `stuck` half. Also part of the tester's wider ask that `why`, `open`, `ventures` and `stuck` share one feasibility test.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 14, 23). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.
