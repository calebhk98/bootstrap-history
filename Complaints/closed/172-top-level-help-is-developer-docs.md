# `simulator.py --help` prints developer documentation

**Status:** closed - --help now shows player-facing descriptions

`python3 sim/simulator.py --help` (the README tells players to run it) prints a module docstring about cli.py / cli_interactive.py / cli_agent.py, `cmd_sweep` placement and `_wilson_interval`, instead of one line per command. It lists `agent`, `plan`, `search`, `run`, `compare`, `sweep`, `sensitivity`, none of which the README mentions.

What it would take: a player-facing description on the argparse parser and per subcommand; keep the developer notes in the module docstring out of `--help`.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.
