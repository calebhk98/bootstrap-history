# Population, carrying capacity, famine and migration are national, not per region

**Status:** closed - people are tracked per tile, fed by their own households, migrate; urban share is read from the regions through one function, bounded by the food each town can draw. What stays open is filed as 674.

Part of Complaint 489 (Population is one national figure, and soldiers, scholars and builders are not checked against food and people).

Reuses the colony stepping in `sim/engine/colonies.py`. Foreign countries need 590 first.

**What is wrong.** `Population` is three national age bands. Land and weather are per region; people are not. Settlement spreads the national figure over held tiles by food potential rather than tracking it. Migration in the labour market moves workers between market areas without moving `Population`. Urban share is the civilisation's fixed `urban_fraction`; nothing evolves it.

**Evidence.** `sim/world/demography.py`, `sim/engine/core.py`; `sim/geography/settlement.py`; `sim/labour/market/migration.py`; only colonies step a separate population.

**Why it matters.** A delta city and a frontier province cannot differ in famine or growth, which the group's regional play needs.

**What it would take.** People per tile or region on the existing tile and market-area structure; migration moves them; urban share follows from them instead of a fixed field.

**Test.** A test with two regions of unequal food: the poor one loses people or sends migrants, the national total is the sum, and urban share is read from the regions.

## What was done

- Region = a tile the nation holds, the unit the economy's household cohorts sit on. `state.population.regions`
  keeps each tile's three age bands (saved by the usual field detection); `sim/world/regional_population.py` steps each as a
  `Population` by the same code as the nation, and `self.population` is their sum. A change made to the nation outside
  the yearly step (settlers leaving, a hazard) is shared among the regions by their people (`keep_to_nation`).
- Each region is fed what its own households ate: `record_food_eaten` also keeps each tile's eaten over need
  (`state.population.regional_eaten_over_need`); a tile with no figure falls back to the nation's, then to its share of
  the farm model's harvest. Relief and epidemic deaths are shared by need and by band.
- Migration: working-age people leave for a bordering region where people ate better, by the labour market's own rule
  (`sim/labour/market/migration.py` `move_shares`, now shared); a day's march costs a day of the origin's subsistence.
  Endemic disease is still the nation's rate for every region.
- The economy is handed the regions' people (`labour.settlement_tiles`), so a region that starves has fewer households next year.
- The engine's demographic step moved from `core.py` to `sim/engine/demographic_recovery.py`; the per-region mechanism is in
  `sim/engine/regional_people.py`.
- Tests: `sim/tests/test_population_per_region_smoke.py` (two regions of unequal food; the nation is the sum; one tile's food cut
  lowers its nutrition and raises its mortality, other tiles unchanged).
- Cost: `python3 -W ignore` six years of rome_100ad (88 tiles), CPU per year before and after: 7.23 s and 7.36 s (loaded
  machine); a region per tile is cheap.
- Urban share from the regions: `Sim.urban_fraction()` (`sim/engine/urban_share.py`) is the only reading of the national share;
  the readers in `sim/labour/labour_population.py` and `sim/engine/agents_port_budget.py` call it; `sim/engine/disease_port.py` (two reads of the file's figure) is left for the disease change to switch to `Sim.urban_fraction()`. Each region's
  town is bounded by the surplus of its farms beyond their own households' need plus what it draws from other regions at
  the carriage cost of grain (`geography.route_costs`: land, river and sea; `sim/world/urban_share.py`, `town_ceilings`),
  a source's surplus shared among the towns that can reach it. A sea or river tile reaches far more farms than an inland
  one (`python3 -m sim.tests.urban_share_opening` prints each civilisation's most-fed share).
- The civilisation's `urban_fraction` is read once, at the opening, to seed each region's share of its people in town
  (`state.population.urban_share_of_people`, shared by what each town can feed); afterwards a region's townspeople are
  that share of its people, never more than its town can feed, so a food shock shrinks the towns. The computed opening share
  is checked against the civilisation's band in `data/world/urban_share_bands.json` (source and confidence per band;
  Han China and the Mexica have none: no source found).
- Tests: `sim/tests/test_urban_share_rules.py` (richer surplus raises the ceiling; cheaper carriage widens the draw; a port
  carries more than a landlocked town with the same hinterland, on built tiles), `sim/tests/test_urban_share_scenario.py`.
- Still open, filed as 674: what makes demand for town people (the state's and landowners' claims on the harvest, trade),
  so the share itself is computed and not only bounded; an urban band that migrants fill; per-tile endemic disease; foreign
  countries (590; their `CountryProfile.urban_fraction` and the strata seed still read the file's figure).

## Research needed

- What sets the urban share of a pre-industrial society from physical inputs (agricultural surplus per farmer, transport cost of grain to the town, the sea and river share, taxes and rents that feed non-farmers), so the share emerges instead of being the civilisation's `urban_fraction`: Wrigley on urban growth and agricultural productivity, Bairoch on city populations, Malanima, Allen on the English agricultural revolution and urbanisation, Hanson on Roman cities. Existing urbanisation models and economic-history simulations would also answer how to model it. Nothing has been opened for this yet.
