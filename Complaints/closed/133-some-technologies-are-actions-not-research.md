# Some technologies are actions, not research

**Status:** closed - dependents name the works they need running (and kilometres of road or railway), lapse down the chain when a work closes, and every reader of held technologies calls one held-and-running method; actions return knowledge, routes and partners and a failed voyage takes its crew, hull and cargo; constructions have a saved register by tile with a capacity that scales cost; the audit's duplicates, the harbour, bath and buoy are settled

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

The engine work the audit listed is built; see Engine progress and Closing.

## Engine progress

`requires_running` is read generically (`sim/engine/projects_running_gates.py`): a start check of kind
`closed`, `running` false while a required work is shut, `open` and `restore` refused, and the yearly
`close_lapsed_dependents` plus a cascade in `close_work` (closure reason `gate_lapsed`). `validate`
rejects an unknown id, a node that cannot run and a cycle. Tests: `sim/tests/test_running_gates.py`
(small fixtures, quick tier). Action results: see the audit, item 4, for what a declared result needs.

## Closing

- One answer to "held and running": `held_and_running` (`sim/engine/held_works.py`) is read by
  `geography_port.held_nodes`, `economy_port_setup`, `foreign_routes`, `coin_carriage` and
  `labour_settlement` (through `LabourWorld`), in place of each building its own set from `done`. A venture
  that is shut is not held.
- Action results: a node's `returns` ({knowledge, route, partner}) is read by the same method
  (`sim/engine/action_results.py`). The sea lanes for the West African coast, the Cape, the open Atlantic
  and the open Pacific now ask for `route:<lane>`, which the expedition that opens each one returns, so
  a lane stays closed while its expedition is not held and running. A partner some node returns is refused
  until held (`partner_gate_refusal`); no authored node returns one yet, because the only foreign economy
  (Han China) trades from the start of the scenario and gating it is a content decision. `validate` checks the kinds and
  that every token a lane asks for is returned (`sim/engine/validate_action_results.py`).
- Loss in a failed voyage: a node's `risks` ({crew, hull, cargo} shares) is taken on a failed attempt
  (`sim/engine/action_loss.py`, called from the failure branch of `_complete`). The three ocean
  voyages declare it; the shares are labelled heuristics, and a hull is the share of its timber, ironwork
  and canvas held in stock until ships are assets.
- Duplicates: every merged-away id resolves to a live survivor and the survivor keeps the gates the
  retired id carried; the merge now rewrites a retired id in `requires_running` as it does in `pre`. The aqueduct and
  sewer pairs are not in the retired list (they are two live nodes in different branches); each
  twin's operating dependents need a work running, and the fire and flood brigades, which stand on the
  aqueduct, now need it running (`sim/tests/test_merged_ids_keep_gates.py`).
- Upkeep for the harbour in hydraulic concrete, the public bath and the buoy: derived as one percent of
  construction labour, labelled a heuristic. The first two had no construction labour authored, so a
  labelled stand-in is stated for each. The buoy needs the harbour running.
- Works register: `state.economy.works` and `works_under_construction` by tile, with a capacity whose cost
  rises by the scalable institutions' convexity (`sim/engine/works.py`, built beside `ways.py` and finished
  on the same yearly beat). `build_work` is an engine method; there is no player command for it yet.
- Gameplay under the gates is unmeasured by the owner's choice (no fingerprint). A slow topic plays Rome to
  a point where the aqueduct closes and its dependents lapse (`sim/tests/test_gated_works_close_in_play.py`); it was written
  and not run, because a whole game could not be built in the authoring container.
