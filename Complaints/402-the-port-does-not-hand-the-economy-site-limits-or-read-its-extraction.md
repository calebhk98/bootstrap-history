# The port does not hand the economy site limits or read back what it extracted

**Status:** open - needs `sim/engine/economy_port*.py` and geography; the economy side is built

The agent economy can now bound a recipe that draws on a site (a production entry with
`extracted_from`): `EconomySetup.site_limits` at the opening and `YearInputs.site_limits` each year
take `sim.economy.types.SiteLimit(recipe_id, tile, capacity_runs_per_year, yield_factor)`. A recipe with
any declared limit then runs only on those tiles, its capacity is capped and its yield follows the
limit (`sim/economy/sites.py`). Each year's `YearOutcome.extraction` gives the runs worked per
(recipe, tile), for geography to deplete by. The economy knows nothing of deposits, grades or reserves.

Nothing fills the limits yet, so every extraction recipe falls back to the labelled heuristic
`UNSITED_EXTRACTION_ANYWHERE`: a mine can open on any tile, never runs out and its yield never falls.
So iron, copper and gold makers are placed wherever labour is cheap, not where ore is.

What it would take (outside `sim/economy/`):
- geography derives, per extraction recipe and tile, the runs a year the site supports and the yield
  factor (grade relative to the recipe's basis, depletion), from its own deposit data;
- `build_setup` (`sim/engine/economy_port_setup.py`) passes `site_limits=...`, and `_inputs`
  (`sim/engine/economy_port_year.py`) passes `site_limits=...` whenever geography's limits change;
- the port stops setting `yield_factor_by_producer` for site-bound recipes (sites.py sets it);
- after `economy.step`, geography reads `outcome.extraction` and depletes.

Tests that pin the economy side: `python3 -m sim.tests --only economy_sites,economy_location`.
