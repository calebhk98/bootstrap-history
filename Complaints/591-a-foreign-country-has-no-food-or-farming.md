# A foreign country has no food or farming: the farm, granary and nutrition chain runs for the home country only

**Status:** open

Part of Complaint 482 (Countries other than the home one are static stubs).

Depends on 590 (a population to feed).

**What is wrong.** The farm, granary and nutrition chain is stepped for the home country alone, so a poor harvest abroad cannot cause a food shortfall.

**Evidence.** The chain runs from `sim/engine/core.py` around `farm_storage.step` and from `sim/world/agriculture*.py`; nothing steps it per foreign country.

**Why it matters.** A country's famine is an input today, so no foreign country can starve, migrate or collapse as a result of weather (CLAUDE.md 4.3).

**What it would take.** Per-country farm and granary state stepped by the code the home country uses, with the nutrition shortfall feeding that country's deaths (590). No content ids in the engine (4.7).

**Test.** A foreign country with a failed harvest shows a food shortfall and a higher death rate than a twin with a good harvest; the home country's numbers are unchanged (state dump or the targeted topics).
