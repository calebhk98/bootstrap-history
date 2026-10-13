# Population is one national figure, and soldiers, scholars and builders are not checked against food and people

**Status:** open

- `Population` is three national age bands (`sim/world/demography.py`, built once in
  `sim/engine/core.py`). Only colonies step a separate population (`sim/engine/colonies.py`). Land and
  weather are per region; people are not, so carrying capacity, famine and migration cannot differ by
  province. Settlement spreads the national figure over held tiles by food potential
  (`sim/geography/settlement.py`) rather than tracking it.
- Migration in the labour market (`sim/labour/market/migration.py`) moves workers between market areas
  without moving `Population`.
- Urban share is the civilisation's fixed `urban_fraction`; nothing evolves it.
- The state's army and officials are budget lines paid at the going wage (`sim/agents/budget.py`). No
  check holds farmers, soldiers, scholars and builders to the working-age people and surplus food that
  exist, and a shortfall does not force the state to disband or levy. The farm-hours shift in
  `sim/labour/labour_allocation.py` acts on society's hours, not on the state's headcounts.
- Literacy lives in three unlinked places (civilisation fields, stratum `literacy`, technology effects)
  and gates hiring, not research output (`sim/labour/labour_capacity.py`, `sim/agents/stratum_year.py`).
- No maize in the crop table (`sim/world/agriculture.py`); irrigation is a stated non-goal there and
  appears only in per-tile crop energy (`sim/geography/food_crops.py`).

Why it matters: the group's core constraint is that a state reallocating tens of thousands to research
and an army must be fed by real surplus, or face famine and revolt (486). Regional variation (a
delta city against a frontier) needs people per region.

What it would take: population per tile or region on the existing tile and market-area structure;
a headcount ledger per country (farm, soldier, scholar, builder, other) checked each year against
working-age people and food; one literacy state per country read by training and research (490).
