"""The composition root of the game and what only the root does.

`core.py` holds `Sim`: the saved state, the random source, the seats and the loop over years. `Sim` has no base classes;
the rules live in the modules (`sim/<module>/`, assembled by `game_assembly.py`), and `Sim` reaches them through views and
commands. The year's steps the root runs itself are plain functions in `year_steps.py`, `year_run.py` and `year_phases.py`;
the seat registry's are in `seat_registry.py`; the root's own facts are declared in `root_facts.py`.

    core, state*, saveload      the root, its saved state and the save round trip
    bridge*                     reads a module still needs from the root
    data, settings*             loading the tree and civilisations, and the game's settings
    ui_port                     what the screens read; economy_port_effects: what mods reach in the economy
    validate*, opening_checks*  data checks and the opening's relationship checks

See `sim/ARCHITECTURE.md` for the shape and the commands that measure it. Enter through `sim/simulator.py`.
"""
