# `changes 10` at 1310 is refused although the game began in 1300

**Status:** closed

Ten years into a run, `changes 10` answers "this run's own record only goes back to 1301 AD, 9 years ago; ask for 9 or fewer". The record starts the year after arrival, so "the last ten years" and "the first ten years" are off by one. Minor, but the refusal reads as a bug.

Reproduces on the current branch:

    printf 'step 10\nchanges 10\nquit\n' | python3 sim/simulator.py play --civ england_1300 --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

What it would take: either include the arrival year in the record, or clamp the request to what exists and say so ("showing 1301 to 1310, the whole record"). Related: 159 (closed: log missing year).

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.
