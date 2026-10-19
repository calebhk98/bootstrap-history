# A foreign country's population never changes and its strata grow by their own rule

**Status:** open

Part of Complaint 482 (Countries other than the home one are static stubs).

**What is wrong.** Only the home country steps a `Population`. A foreign country is a `CountryProfile` read through `CountryWorld`, and its headcount is the seeded figure forever.

**Evidence.** `population_total()` returns `self.profile.population` (`sim/agents/country_view.py`); nothing assigns it after seeding (`grep -rn "profile.population\s*=" sim`). Home strata are held to the population the engine counts (`sim/agents/strata_seed.py`, `strata_observed.py`); a foreign country's strata grow by their own rule from the seeded figure.

**Why it matters.** Births and deaths abroad are inputs, not outcomes (CLAUDE.md 4.3, section 2: every mechanism usable by any actor).

**What it would take.** One `Population` per country (`sim/world/demography.py`, built once in `sim/engine/core.py` for the home country), stepped by the code the home country uses, and the strata reconciled to the people counted there as the home strata are. Famine and plague arrive with 591 and 592; this piece makes births and deaths step.

**Test.** A new test topic: a seeded foreign country's population changes over a run with no hand assignment; its strata sum to the people counted; a country whose births are removed in the fixture declines.
