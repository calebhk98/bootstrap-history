# `play --session FILE` for a new file refuses without `--civ`, contrary to the README

**Status:** closed - the guard against a mistyped --session path is deliberate; the README now starts a saved game with --civ

The README shows `python3 sim/simulator.py play --session mygame.json` as a way to start. With no save at that path: "no --civ given, so I do not know what game you meant". Plain `play` starts the default civ.

What it would take: start the default civ (as `play` does), or show `--civ` in the README example.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.
