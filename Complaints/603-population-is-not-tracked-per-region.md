# Population, carrying capacity, famine and migration are national, not per region

**Status:** open

Part of Complaint 489 (Population is one national figure, and soldiers, scholars and builders are not checked against food and people).

Reuses the colony stepping in `sim/engine/colonies.py`. Foreign countries need 590 first.

**What is wrong.** `Population` is three national age bands. Land and weather are per region; people are not. Settlement spreads the national figure over held tiles by food potential rather than tracking it. Migration in the labour market moves workers between market areas without moving `Population`. Urban share is the civilisation's fixed `urban_fraction`; nothing evolves it.

**Evidence.** `sim/world/demography.py`, `sim/engine/core.py`; `sim/geography/settlement.py`; `sim/labour/market/migration.py`; only colonies step a separate population.

**Why it matters.** A delta city and a frontier province cannot differ in famine or growth, which the group's regional play needs.

**What it would take.** People per tile or region on the existing tile and market-area structure; migration moves them; urban share follows from them instead of a fixed field.

**Test.** A test with two regions of unequal food: the poor one loses people or sends migrants, the national total is the sum, and urban share is read from the regions.
