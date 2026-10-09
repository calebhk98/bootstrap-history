# Some technologies are actions, not research

**Status:** partly - done: data fixes of the audit; a node field `requires_running` (works that must be built and open) gating beginning, opening, effects and open dependents, with lapse down the chain when a work closes and no softlock exemption for a work others rely on; `requires_ways` (kilometres of road or railway built, read through geography's `built_km`) as the size and place of a built work; the data step: the operating dependents of the grid, telegraph, railway, harbour, aqueduct, sewer and road network now name the works they need running, and railway services, block signalling and electric traction also ask for built track (`python3 -m unittest sim.tests.test_dependents_need_running` lists them). Remaining: gameplay under these gates is unmeasured (the owner chose no fingerprint), the duplicate-id pairs of the audit gate only the surviving id, the harbour pozzolana, public bath and buoy have no upkeep to gate on, a general works register on tiles other than ways, action results other than living stock, loss of hull, crew and cargo in a failed voyage

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

## Engine progress

`requires_running` is read generically (`sim/engine/projects_running_gates.py`): a start check of kind
`closed`, `running` false while a required work is shut, `open` and `restore` refused, and the yearly
`close_lapsed_dependents` plus a cascade in `close_work` (closure reason `gate_lapsed`). `validate`
rejects an unknown id, a node that cannot run and a cycle. Tests: `sim/tests/test_running_gates.py`
(small fixtures, quick tier). Action results: see the audit, item 4, for what a declared result needs.
