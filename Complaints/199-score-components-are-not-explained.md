# `score` does not say what resilience or institutions count; both read as contradictory

**Status:** open

- Resilience is reported high whatever the hazard screen says: at 1310 with nothing built, raw 4 gives normalized 0.960 (reproduced below), while `risk` shows severe staff loss for the coming famine and plague and an unhedged corpus. In the tester's run it rose to 0.994, then 0.998 while Black Death staff loss was still 29 to 40 percent per wave, many built technologies were unhedged, and the household was heavily leveraged.
- Institutions stayed exactly 0 through 1350 despite a finished written corpus, an operating sanitation network, and trained engineers and machinists; it became 6 only after a university, a collegium and the corpus were all operating. If the score counts only opened formal institutions (the corpus was finished but closed at that point) the screen does not say so.

Reproduces on the current branch (resilience part):

    printf 'step 10\nscore\nquit\n' | python3 sim/simulator.py play --civ england_1300 --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

The score screen prints only raw and normalized values and weights. What it would take: one line per component naming its inputs ("resilience: mitigations in force against the hazards ahead, weighted by ..."), and for institutions the list of what counts and what is finished but closed. Related: 183 (closed: score when the goal is missed).

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.
