# Electropolishing hard-requires the national power grid

**Status:** closed - pinned by sim/tests/test_bloomery_bar_and_gates.py

**Source:** `reports/PLAYTEST_LOG_ROME_100_BLIND.md` observation 241.

## What is wrong

`el2_electropolishing_etching_surface_finish` has a `current` requirement group
whose only option is `power_grid`. Small-scale electropolishing runs on a DC
cell or a dynamo; the node is gated as if it needed grid-scale supply. It sits
on the goal's critical path (it unlocks `gp_whisker_forming`), so it drags the
grid's long floor and high failure chance into the transistor route.

## Evidence

- `data/tech_tree.json`, node `el2_electropolishing_etching_surface_finish`,
  `req_any` group `current`: the options are `power_grid` alone.
- Its predecessor `el2_electroplating_and_electrorefining` accepts a shunt
  dynamo or a metal-layer rectifier for the same job.
- `python3 sim/simulator.py why el2_electropolishing_etching_surface_finish`
  lists the grid inside the full chain behind it.

## Why it matters

An unphysical gate hides a real route (bench current) and lengthens the
critical path for no causal reason. Gates should be physical, not
chronological or scale-inflated.

## What it would take

Give the `current` group the same options as electroplating (dynamo or
rectifier) and keep `power_grid` as one option, not the only one. Edit the
branch file in `data/branches/`, rebuild with `python3 sim/treetool.py merge`,
run `python3 sim/simulator.py validate`, and add a test that the node is
startable with a dynamo and no grid.

Also reported (Han China 100 AD fog playtest, tester item(s) 183, 179; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): the tester's two transistor branches were both blocked on electropolishing's `power_grid` gate after the grid was lost; a small laboratory with working workshop power, a 3 MW hydro station and a shunt dynamo could not do chemical surface preparation. The same gate shape on zinc and the commutator is 228.

## Fixed

The node listed `power_grid` twice: in `pre` and as the only option of its
`current` group. Both are gone as hard requirements. `pre` no longer names
`power_grid`, and the `current` group now offers `power_grid`, a shunt dynamo
or a metal-layer rectifier, so a bench cell or a small station with a dynamo
is enough. `el2_electroplating_and_electrorefining`, which stays a
prerequisite, already demands one of the two small current sources. The
test checks that the group offers a dynamo alongside the grid.
