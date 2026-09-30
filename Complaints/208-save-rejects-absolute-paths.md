# `save` refuses absolute paths

**Status:** open

`save /tmp/x.json` is refused: "a save file must be a relative path, not an absolute one. Try save mygame.json". The tester assumed it was deliberate but found it an extra step when exporting a save to a chosen place.

Reproduces on the current branch:

    printf 'save /tmp/x.json\nquit\n' | python3 sim/simulator.py play --civ england_1300 --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

What it would take: either accept absolute paths (the player owns the machine), or keep the rule and say where a relative name is saved and how to move it (`options` prints the save location). If the restriction guards the agent/JSON protocol, it could apply only to that path.

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.
