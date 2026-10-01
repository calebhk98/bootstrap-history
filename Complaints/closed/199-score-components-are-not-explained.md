# `score` does not say what resilience or institutions count; both read as contradictory

**Status:** closed - `score` prints a `counts` sentence per component, lists institutions finished but closed, and says what moved in each component since your last `score`

- Resilience is reported high whatever the hazard screen says: at 1310 with nothing built, raw 4 gives normalized 0.960 (reproduced below), while `risk` shows severe staff loss for the coming famine and plague and an unhedged corpus. In the tester's run it rose to 0.994, then 0.998 while Black Death staff loss was still 29 to 40 percent per wave, many built technologies were unhedged, and the household was heavily leveraged.
- Institutions stayed exactly 0 through 1350 despite a finished written corpus, an operating sanitation network, and trained engineers and machinists; it became 6 only after a university, a collegium and the corpus were all operating. If the score counts only opened formal institutions (the corpus was finished but closed at that point) the screen does not say so.

Reproduces on the current branch (resilience part):

    printf 'step 10\nscore\nquit\n' | python3 sim/simulator.py play --civ england_1300 --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

The score screen prints only raw and normalized values and weights. What it would take: one line per component naming its inputs ("resilience: mitigations in force against the hazards ahead, weighted by ..."), and for institutions the list of what counts and what is finished but closed. Related: 183 (closed: score when the goal is missed).

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.

Also reported (Han China 100 AD fog playtest, tester item(s) 197; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): resilience fell from 3 to 2 (raw) between 325 and 350 AD with the dispersed corpus running and no explanation; literacy 21 percent and institutions 13 stayed flat for 75 years. The tester asks for a delta line per component on `score`. Reproduces: untested (late game).

**Remains:** None. A second `score` prints, under each component, its raw value and the normalized change since the previous `score` (kept in `scenario.score_last_seen`; `sim/engine/proto/score_change.py`). Regression test: `sim/tests/test_screen_text_defects.py`.
