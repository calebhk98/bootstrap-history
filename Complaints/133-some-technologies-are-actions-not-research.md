# Some technologies are actions, not research

**Status:** partly - one expedition now returns held stock; the audit of the rest is not done

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

## Progress

`exp_import_draught_animals` is an action (a voyage with crews and risk) and now says what it
returns: a node's `grants` adds a founding herd to the held stock when it completes, and the Mexica
gate on draught-animal work lifts on holding the animals (Complaints/365). Other expeditions that
return living stock (`exp_transplant_botany`, `fud_pepper_cultivation`, `ag2_tea_voyage`,
`ag2_coffee_voyage`) can use the same `grants` field. The audit of grids, networks, colonies and
surveys, and the construction class, are untouched.
