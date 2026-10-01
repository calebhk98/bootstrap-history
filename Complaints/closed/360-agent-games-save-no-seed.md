# An `agent` game saves no seed, so a resumed agent game cannot report it

**Status:** closed

The random generator's full state is saved and restored (`proto/saveload.py`), so a resumed game continues the same stream. The seed number is saved from `sim.seed`, which only `play` sets (`cli_interactive.py`); `agent` (`cli_agent.py`) never sets it, so its saves hold no seed and `--session` games report none.

Fix: set the seed in `agent`, and a test that a saved and loaded game of either kind reports the seed it started with.
