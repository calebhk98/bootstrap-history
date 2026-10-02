# `save` refuses absolute paths

**Status:** closed

`save /tmp/x.json` is refused: "a save file must be a relative path, not an absolute one. Try save mygame.json". The tester assumed it was deliberate but found it an extra step when exporting a save to a chosen place.

Reproduces on the current branch:

    printf 'save /tmp/x.json\nquit\n' | python3 sim/simulator.py play --civ england_1300 --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

What it would take: either accept absolute paths (the player owns the machine), or keep the rule and say where a relative name is saved and how to move it (`options` prints the save location). If the restriction guards the agent/JSON protocol, it could apply only to that path.

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.

Also reported (Han China 100 AD fog playtest, tester item(s) 2, 111, 181, 198; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): `save /workspace/.../han-fog-year-225.json` refused as absolute on five occasions; the tester exported a checkpoint by copying the autosave file after `quit`. Also: a relative manual `save` does not change where the live session is written (the intro says so only after a quit), the manual save landed in the working folder rather than a configured save folder, and resuming a named checkpoint with `--session han-fog-year-300.json` overwrote it with year 325 (by design: the session file is written after every command). A warning when resuming a named checkpoint, or a dated snapshot on `quit`, would keep exports distinct. Reproduces: yes (absolute path refused; replayed in a Han game).

Also reported (final playtests, A; `Complaints/reports/final-playtests-triage.md`): asks for clear manual export and import instructions for saves so a run can be moved between containers.

**Resolution:** a typed `save` in `play` accepts absolute paths (the JSON protocol still refuses them), prints the full path it wrote, says the live session file is a separate file that keeps autosaving, and marks the snapshot as a checkpoint so resuming it with `--session` forks a new live file instead of overwriting it. The same message and the README say how to move a save between machines or containers (copy the file and its `.meta.json`, then `play --session <copy>`). Tests: `sim/tests/test_menu_seed_choice.py`, `sim/tests/test_menu_seed_and_saves.py`.
