# Solved copper and silver costs are far below the old book figures

**Status:** open

With the book gone, Rome's node-cost table (`data.load(civilization_id="rome_100ad")`) prices copper_kg at about 0.7 coin units against the old 21.6 and silver_kg at about 27 against 1714; wheat fell from 0.70 to 0.14 and iron_bar from 5.4 to 0.69. The old book numbers are not a target (CLAUDE.md 4.5), but copper at a few labour hours per kilogram and silver at roughly a hundred should be audited against the deposit grades, smelting labour and fuel in `data/production/` before they are trusted, because the shift moved every node's cost (see Complaints/287).

Measure: `python3 sim/solve_prices.py --why copper_kg` and `--why silver_kg`.

What it would take: check ore grade, recovery, labour per tonne and fuel for the chosen copper and silver recipes; check the price solver is not taking an ungated cheap route for Rome.
