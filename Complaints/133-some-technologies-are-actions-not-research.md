# Some technologies are actions, not research

**Status:** partly - the data fixes of the audit are done (living stock returned by the American post, upkeep on constructions that had none); the engine work in `Complaints/reports/action-and-construction-node-audit.md` (a running gate on dependents, works with a place and a size, action results other than stock, lapse of a completed work) remains

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

`exp_import_draught_animals` is an action (a voyage with crews and risk) and says what it returns: a
node's `grants` adds a founding herd to the held stock when it completes, and the Mexica gate on
draught-animal work lifts on holding the animals (Complaints/365). The tea, coffee, sugar and pepper
voyage nodes already carry `grants`, as do the cashmere, jute, angora, hop and pyrethrum stock nodes.
`exp_americas_factory` now grants seed stock of potato, maize and cacao, and `fud_potato`, `fud_maize`
and `fud_cacao` hold it, with rows in `data/world/living_stock.json` and production entries in
`data/production/95_living_stock_crops.json`.

Constructions that had no upkeep now carry a derived one (a stated share of construction labour,
labelled a heuristic) so they are ventures that can be opened and closed: the semaphore chain, the
aqueducts and latrines, trunk telephone lines, Chain Home, electric street lighting, sand filtration,
separate sewage, activated sludge, the isolation hospital and the stormwater-separated sewer. Two
audit entries have no construction labour to take a share of (`sea_harbours_pozzolana`,
`hom_public_bath`) and are left until they are given a build.

What remains is engine work, listed in the audit: dependents that require a work to be running, a
place and a size for built works, action results other than living stock, and lapse of a completed
work.
