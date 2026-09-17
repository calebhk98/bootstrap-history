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
nutrition as the mechanism linking food to births and deaths. Nothing in
`sim/engine/` imports this package yet - see `demography.py`'s own docstring
for the wiring this is standing in for (`Sim._demographic_recovery`) and for
what would have to change for that wiring to happen. Until that day this
package is inert: importing it changes no behaviour anywhere else in the
repository, and none of its tests touch a real `Sim` or a save file.
"""
