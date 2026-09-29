# Electropolishing hard-requires the national power grid

**Status:** open

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
