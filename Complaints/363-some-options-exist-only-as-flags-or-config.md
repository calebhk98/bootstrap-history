# Some options exist only as command-line flags or config entries, and `agent` mode has no options at all

**Status:** open

The main menu's options cover the save folder, width, rows per page, the welcome text and display units; the New Game wizard remembers civilisation, kit, fog, estimates, mortality, goal and horizon. `commission_display` and `default_seed` can be changed only in the config file; events on or off and deterministic mode only by flag; `agent` mode has no options menu, and the `ROME_SAVE_DIR`/`ROME_SIM_CONFIG` environment variables are undocumented in-game.

Fix: every setting a player can change has an entry in the options screen (and an `options` command in `agent` mode), generated from the settings table so a new setting appears without editing the menu.
