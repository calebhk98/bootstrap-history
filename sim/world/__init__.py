"""The world, apart from the founder.

`sim/engine/` is the founder's simulation: one household, one set of books,
one player. Everything the founder is NOT - the population that supplies
labour, the land that grows food, eventually the other actors who compete
with the founder for both - belongs here instead, built and proven on its
own before anything in `engine/` is asked to depend on it.

WHY A SEPARATE PACKAGE RATHER THAN A NEW FILE IN `engine/`. Two reasons, one
procedural and one architectural. Procedurally: other agents are editing
`sim/engine/`, `data/branches/`, `data/production/` and `data/tech_tree.json`
concurrently with this package's construction, and a module that imports
nothing from those paths cannot be broken by their edits or break their
tests, whichever lands first. Architecturally: `docs/architecture/
ENDOGENOUS_COSTS_AND_DOMAINS.md` (Milestone 4) and `docs/architecture/
CURRENT_CODE_ARCHITECTURE_REVIEW.md` (SS6.5, 6.7) both describe demography and
agriculture as domains the rest of the simulation should come to depend on,
not features bolted onto `Sim`. A module that can only be exercised by
constructing a full `Sim` was never going to get a fast, focused test suite;
one importable on its own, with no engine dependency at all, can.

CURRENT CONTENTS. `demography.py`: age-cohort population dynamics, with
nutrition as the mechanism linking food to births and deaths.

THIS PACKAGE IS NO LONGER INERT, AND THAT PARAGRAPH USED TO SAY IT WAS.
`sim/engine/core.py` now imports `demography` and holds a real
`Population` on `Sim`, so the three age cohorts are live state that saves
and loads, and `Sim._demographic_recovery` steps them rather than running
the old scalar `pop_deficit` and its exponential recovery clock, both of
which are deleted. A hazard's mortality is now applied unevenly across the
cohorts, so two shocks of equal headcount diverge afterwards depending on
who died - a property the scalar model could not express at all.

What that means for anyone editing here: this package's modules are still
importable and testable on their own, with no engine dependency in this
direction, and their own tests still touch no `Sim` and no save file. But a
change to `demography.py`'s shape now reaches the engine, so it is no longer
free. Run the full suite, not just this package's tests.

`agriculture.py` IS WIRED IN TOO, and this paragraph used to say the
opposite. It claimed the module was "genuinely inert - nothing in
`sim/engine/` imports it yet" and that `Sim._demographic_recovery` fed
`Population.step` a labelled stand-in for food supply rather than
`Storage.step`'s real output. Both halves were false by the time anyone read
them: `sim/engine/core.py:33` does `from world import agriculture`, and
`_demographic_recovery` computes a real year of `agriculture.Storage.step`
from land, labour and weather, which is what lets a bad year drive
`nutrition_ratio` below 1.0. The `agriculture_wiring` test topic exists
precisely to pin that seam, which neither module's own standalone suite can
see, because the seam is not inside either of them.

So the same rule now applies to `agriculture.py` as to `demography.py`: it
stays importable and testable on its own, and a change to its shape is no
longer free. Run the full suite.

`agriculture.py` is also now a composition point over `agriculture_yield.py`
(the production function), `agriculture_storage.py` (the granary) and
`agriculture_labour.py` (sizing a farm from a population); it keeps the
declared constants and the crop, soil, rotation and toolkit tables, and
re-exports everything, so no caller changed. See its own docstring for why
that split looks different from the others in this package.
"""
