"""The world, apart from the founder.

`sim/engine/` is the founder's simulation: one household, one set of books,
one player. Everything the founder is NOT - the population that supplies
labour, the land that grows food, eventually the other actors who compete
with the founder for both - belongs here instead, built and proven on its
own before anything in `engine/` is asked to depend on it.

WHY A SEPARATE PACKAGE RATHER THAN A NEW FILE IN `engine/`. Two reasons, one
procedural and one architectural. Procedurally: this package imports nothing
from `sim/engine/`, `data/branches/`, `data/production/` or
`data/tech_tree.json`, so it cannot be broken by edits to those paths, nor
break their tests, however much work proceeds on them in parallel.
Architecturally: `docs/architecture/ENDOGENOUS_COSTS_AND_DOMAINS.md`
(Milestone 4) and `docs/architecture/CURRENT_CODE_ARCHITECTURE_REVIEW.md`
(SS6.5, 6.7) both describe demography and agriculture as domains the rest of
the simulation should come to depend on, not features bolted onto `Sim`. A
module that can only be exercised by constructing a full `Sim` was never
going to get a fast, focused test suite; one importable on its own, with no
engine dependency at all, can.

CURRENT CONTENTS. `demography.py`: age-cohort population dynamics, with
nutrition as the mechanism linking food to births and deaths.

BOTH `demography.py` AND `agriculture.py` ARE WIRED INTO THE ENGINE.
`sim/engine/core.py` imports `demography` and holds a real `Population` on
`Sim`, so the three age cohorts are live state that saves and loads, and
`Sim._demographic_recovery` steps them. A hazard's mortality is applied
unevenly across the cohorts, so two shocks of equal headcount diverge
afterwards depending on who died - a property a single population scalar
could not express.

`sim/engine/core.py:33` does `from world import agriculture`, and
`_demographic_recovery` computes a real year of `agriculture.Storage.step`
from land, labour and weather, which is what lets a bad year drive
`nutrition_ratio` below 1.0. The `agriculture_wiring` test topic pins that
seam, which neither module's own standalone suite can see, because the seam
is not inside either of them.

What that means for anyone editing here: this package's modules are still
importable and testable on their own, with no engine dependency in this
direction, and their own tests still touch no `Sim` and no save file. But a
change to either module's shape reaches the engine, so it is not free to
make in isolation - run the full suite, not just this package's tests.

`agriculture.py` is also a composition point over `agriculture_yield.py`
(the production function), `agriculture_storage.py` (the granary) and
`agriculture_labour.py` (sizing a farm from a population); it keeps the
declared constants and the crop, soil, rotation and toolkit tables, and
re-exports everything, so no caller changed. See its own docstring for why
that split looks different from the others in this package.
"""
