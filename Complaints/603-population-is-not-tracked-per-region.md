# Population, carrying capacity, famine and migration are national, not per region

**Status:** partly done. People are tracked per tile, fed by their own households, and migrate; urban share is still the civilisation's fixed `urban_fraction`.

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
- Tests: `sim/tests/test_population_per_region.py` (two regions of unequal food; the nation is the sum; one tile's food cut
  lowers its nutrition and raises its mortality, other tiles unchanged).
- Cost: `python3 -W ignore` six years of rome_100ad (88 tiles), CPU per year before and after: 7.23 s and 7.36 s (loaded
  machine); a region per tile is cheap.
- Still open: urban share from the regions; per-tile endemic disease; foreign countries (590).

## Research needed

- What sets the urban share of a pre-industrial society from physical inputs (agricultural surplus per farmer, transport cost of grain to the town, the sea and river share, taxes and rents that feed non-farmers), so the share emerges instead of being the civilisation's `urban_fraction`: Wrigley on urban growth and agricultural productivity, Bairoch on city populations, Malanima, Allen on the English agricultural revolution and urbanisation, Hanson on Roman cities. Existing urbanisation models and economic-history simulations would also answer how to model it. Nothing has been opened for this yet.
