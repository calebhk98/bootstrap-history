# Some technologies are actions, not research

**Status:** open

Several tree nodes model something you do or build as if it were something
you learn. Examples: an expedition to the Americas is a voyage (ships,
crews, supplies, time at sea, risk), not a research project; a country-wide
power grid is partly engineering knowledge but mostly construction (copper,
towers, generation, labour, years). Nodes that depend on these should depend
on the voyage having happened or the grid existing, not on having
"researched" them.

## Why it matters

A research node completes once and is then known everywhere; an action or a
build has a location, a cost that scales with size, and can be lost. Treating
them as research lets a player "know" a continent or a grid into existence.

## What it would take

- Classify nodes into knowledge (research), construction (a built work with
  capacity and upkeep) and action (an expedition or event with risk).
- Construction and action nodes run through the existing project and venture
  machinery; dependents check for the built work or the completed action.
- Audit the tree for nodes of each kind (expeditions, grids, networks,
  colonies, surveys).
