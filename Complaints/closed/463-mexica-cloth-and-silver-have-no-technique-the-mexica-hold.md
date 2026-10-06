# Mexica cloth and silver have no technique the Mexica hold

**Status:** closed - tex_backstrap_loom is held by mexica_1500, with cotton and maguey backstrap fabric, backstrap cloth and charcoal-smelted silver entries in data/production/96_mesoamerican_fibre_and_silver.json; sim/tests/test_mexica_cloth_and_silver.py

`python3 sim/simulator.py validate` (the basket-supply check, `sim/engine/civ_basket_check.py`) lists goods each civilisation's households want but cannot make or import, with a reason per good in the civilisation file's `unsupplied_basket_goods`. Most reasons are history (no maize in the Old World, no Portland cement before the industrial age). Two in `data/civilizations/mexica_1500.json` are gaps in the model instead:

- `cloth_kg` and `fabric_kg`: Mexica cloth was woven on the backstrap loom, which is not a node in the tree; the loom nodes that gate the textile chain are Old World frame looms. So Mexica households, who wore cotton and maguey-fibre cloth, have no supply.
- `silver_kg`: the only silver recipe is mercury amalgamation, a colonial process; native and smelted silver was worked before contact.

What it would take: a backstrap-loom node held by the Mexica start, with cotton and maguey fibre entries gated on it; and a smelting or native-silver entry for silver that pre-contact metallurgy supports. Each needs a kb source. When fixed, delete the two reasons from `unsupplied_basket_goods` (the check reports a stale reason as an error).
