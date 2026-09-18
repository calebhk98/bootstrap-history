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

`agriculture.py` remains genuinely inert - nothing in `sim/engine/` imports
it yet, and `Sim._demographic_recovery` currently feeds `Population.step` a
labelled stand-in for food supply rather than `Storage.step`'s real output.
See that stand-in's own comment for the unit mismatch whoever wires it in
must resolve first.
"""
