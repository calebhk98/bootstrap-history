# Mods cannot add "why" figures or screen rows through data

**Status:** closed - figures are declared in data/ui/figures.json (base and mods), and the goods a mine supplies come from the resource catalogue; sim/tests/test_complaint_423_figures_and_mine_goods_from_data.py. The `buy` verbs (forest, nitre, school, ...) remain code: each is an action with its own handler, not a list of materials, and `buy mine`/`quote mine` already accept any priced material.

The `figures` / `why <figure>` inspector (`sim/ui/figures.py`) is a registry, but registration is Python inside `sim/ui`, so a mod that adds a quantity (a new hazard, a new resource) cannot add a figure for it. Likewise `sim/ui/proto/economy.py` keeps a fixed tuple of mine materials for demand and `buy` accepts a fixed set of targets.

What it would take: a data file (for example `data/ui/figures.json`, mod-extendable like other world data) naming each figure's id, label, unit and the public `Sim` attribute or method it reads, loaded by `sim/ui/figures.py`; and the engine publishing which materials are mined and which things can be bought, so the UI reads the lists instead of naming them. The data files live outside `sim/ui`.

Related: 95, 118, 122.
