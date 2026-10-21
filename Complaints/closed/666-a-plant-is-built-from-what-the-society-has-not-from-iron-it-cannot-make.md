# A plant is built from what the society has, not from iron it cannot make

**Status:** closed. A capital part carries ordered `build_alternatives` (`data/production/_SCHEMA.md`, CAPITAL). The solver (`sim/engine/capital_builds.py`, `solve_prices_core.py`, `solve_prices_round.py`) treats a part as buildable when any build is and prices it from the first whose materials are priced; `makeable_prices` keeps a good whose plant has a buildable alternative and `economy_port_setup` folds each recipe's plant from the first buildable build (`sim/economy/plant_builds.py`). Tests: `sim/tests/test_complaint_666_plant_build_alternatives.py`.

In Mexica 1500 the opening left charcoal, coal, leather, bread, alum, bone ash, copper and silver unpriced (and heat only through a fallback), because their recipes' capital `build_materials` list `iron_bar_kg`, which Mexica cannot make, and the solver treated plant build materials as hard dependencies. Historically they made charcoal, tanned leather and smelted copper without iron. Measure: build `build_setup(unopened_sim(civ="mexica_1500")).opening_prices` and look for `charcoal_kg`.

Done: alternatives (wooden tools of the same mass in place of the iron bar, with the extra carpenter hours and shorter life) on charcoal, wood tar, coal, leather and bone ash. Every figure is a labelled heuristic (conf D, `retire: Complaint 666`); no source was found, so a sourced figure (hours to hew a wooden tool against forging an iron one, and how long each lasts) is what retires them.

Left open: `bronze_kg` stays unpriced in Mexica because it lacks tin, not iron; other plants naming iron fittings carry no alternative until a society that cannot make iron reaches them.
