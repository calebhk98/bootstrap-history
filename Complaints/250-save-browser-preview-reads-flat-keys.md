# The load browser shows "None AD" and 0 technologies for a valid save

**Status:** open

The main-menu "Load a saved game" list shows a saved game as year `None AD` and `0` technologies, although loading it restores the right year and techs.

Cause (measured): `settings.list_saves` (`sim/engine/settings.py`) reads `year`, `capital`, `reputation`, `scholars`, `artisans` and `done` from the top level of the JSON, but a save is nested (`scenario.year`, `household.capital`, `household.done`, `projects.done`). Only the underscore fields (`_civ`, `_goal`, `_fog`) are read from where they live; `founder_alive` and `dead_reason` are nested too (under `founder`) and silently default. Reproduce:

    printf 'state\nquit\n' | python3 sim/simulator.py play --civ rome_100ad --seed 1 --session /tmp/x/r1.json
    python3 -c "import sys; sys.path.insert(0,'.'); from sim.engine import settings; print(settings.list_saves('/tmp/x'))"

prints `'year': None ... 'capital': None` and an empty `done`. Reproduces now: yes.

Why it matters: the browser is how a player picks which save to resume (the checkpoint files are the only way to keep a run between containers); a wrong preview makes every save look empty or corrupt. A second tester also asked for more on the row (civilisation, founder status, goal, save date) and for a clear warning when a file is unreadable instead of zeroes.

What it would take: read the nested fields the save really has (a test that saves a played game and lists it), show an explicit "unreadable" row for files that do not parse, and add goal, founder alive/dead and save date to the row.


Found in the final blind playtests of this branch (Rome 100 AD fog plus fuzzy, immortal, won 358 AD; tester bug 1; tester also asks for save metadata and export advice (see 208, 185)). Reports: `Complaints/reports/playtest-rome-fog-fuzzy-demo.md`; triage: `Complaints/reports/final-playtests-triage.md`.
