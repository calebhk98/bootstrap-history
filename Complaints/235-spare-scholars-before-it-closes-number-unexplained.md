# "Bone setting has 1.2 spare scholars before it closes" appears with only the founder as a scholar

**Status:** partly - the spare figure now comes with held, in use and allowance (full-time equivalents) and a one-line explanation on `state`.

After opening bone setting and buttons in a new Han game (one scholar and one craftsman, both the founder, no employees), `state` prints "Bone setting has 1.2 spare scholars before it closes" and
"Button with eyelet has 1.5 spare craftsmen before it closes". The headline (`projects_staffing.py`, around line 301) reports `room` in people, but the household holds one scholar and one craftsman, so the number
cannot be a headcount and the page that explains it (`labour`) does not reconstruct it. The tester could not work out which loss would close a concern.

    printf 'start med_bone_setting\nstep\nopen med_bone_setting\nstate\nquit\n' | python3 sim/simulator.py play --civ han_china_100ad --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

What it would take: print free FTE, required FTE and the named people behind the margin, or say which single departure closes it; explain the fractional rounding once. Closed complaint 1 addressed "overcommitted" wording; the new headline introduced the number.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 24, 7). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.

Also reported (Han China 100 AD fog playtest, tester item(s) 82; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): `labour` said the household could hold at most 6.2 people across the lettered trades while the roster already exceeded that across engineers, chemists, machinists, scholars and scribes, and one more scholar was then hired successfully; the label does not match the rule it enforces (a scholar market ceiling versus trained staff). Not replayed.

**Remains:** the `labour` ceiling label (6.2 people across lettered trades) that disagrees with the rule it enforces was not replayed or changed.
