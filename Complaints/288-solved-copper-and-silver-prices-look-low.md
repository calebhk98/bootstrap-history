# Solved copper and silver costs are far below the old book figures

**Status:** partly - ore dressing and roasting are now costed for copper and lead; the remaining gap to attested labour is filed in 410

With the book gone, Rome's node-cost table (`data.load(civilization_id="rome_100ad")`) prices copper_kg at about 0.7 coin units against the old 21.6 and silver_kg at about 27 against 1714; wheat fell from 0.70 to 0.14 and iron_bar from 5.4 to 0.69. The old book numbers are not a target (CLAUDE.md 4.5), but copper at a few labour hours per kilogram and silver at roughly a hundred should be audited against the deposit grades, smelting labour and fuel in `data/production/` before they are trusted, because the shift moved every node's cost (see Complaints/287).

Measure: `python3 sim/solve_prices.py --why copper_kg` and `--why silver_kg`.

What it would take: check ore grade, recovery, labour per tonne and fuel for the chosen copper and silver recipes; check the price solver is not taking an ungated cheap route for Rome.

## Progress

- [x] Audited the chain (`python3 sim/solve_prices.py --civ rome_100ad --why copper_kg`): mining is priced from the deposits (rent on `copper_ore_kg` is the marginal deposit's cost), smelting and charcoal were already costed, but crushing, washing and roasting the ore were not. `copper_kg` now carries dressing and roasting labour with a stated basis (conf D rates). Copper rose from about 2.6 to about 3.7 labour hours per kg for Rome (England 2.2 to 3.2, Norse 2.1 to 3.2, Han 2.6 to 3.7, Mexica 2.0 to 3.1).
- The recipe's 50 tonnes of ore per tonne of copper is about twice the rock the deposits imply at their grades and the 80% recovery (about 28 tonnes); not changed (it would make copper cheaper), worth a grade audit.
- Silver: see 143, 337 and 410.
