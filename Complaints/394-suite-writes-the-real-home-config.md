# The test suite writes the developer's real settings file

**Status:** open

Running the suite changes `~/.rome-sim-config.json`, the player's own settings (`sim/engine/settings.py`, `config_path()`). After one run on a fresh machine it held `default_horizon` 9999, `default_goal` `point_contact_transistor` and `default_fog` true, none of which the developer chose. Every later game and every `options` screen then starts from those values, and two runs of the same command give different `options` output depending on whether the suite ran in between.

Evidence: note the file's contents and modification time, run `python3 -m sim.tests`, compare. Which test writes it was not narrowed down; `python3 -m sim.tests --only <topic>` with the file's modification time checked after each topic finds it.

What it would take: the test harness points `ROME_SIM_CONFIG` (and `ROME_SAVE_DIR`) at a temporary directory for every test, so no test can touch the real home directory.
