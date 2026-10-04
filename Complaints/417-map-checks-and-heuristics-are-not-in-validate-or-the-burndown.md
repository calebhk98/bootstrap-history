# Map checks and heuristics are not in validate or the burndown

**Status:** open

Geography's coefficients live as data (`data/world/geography/parameters/*.json`, each with kind, source, confidence and reason) so mods and other maps can change them. `python3 sim/constants.py --burndown` does not read them, so the heuristic queue undercounts; and `python3 sim/simulator.py validate` does not run the map's own checks (`api.problems()`), so a broken mod map is only found when a query fails.

What it would take: the burndown lists `sim.geography.parameters.heuristics(map)`; validate prints `api.problems()` for the base map with the active mods.
