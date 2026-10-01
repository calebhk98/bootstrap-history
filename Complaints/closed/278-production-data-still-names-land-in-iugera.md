# Production data still names land in iugera

**Status:** closed - production data, the tree's land-consuming nodes and the solver all use `hectare_land` and `land_hectare_years`; the iugerum conversion is gone; tests test_price_solver_land.py

The land model works in hectares (`sim/world/land.py`), but the production
data and the price solver still use the Roman unit: the material
`iugerum_land` and the recipe field `land_iugera_years` (see
`data/production/_SCHEMA.md`, `sim/solve_prices_core.py`,
`sim/solve_prices_report.py`). The solver multiplies the land rent by
`land.IUGERUM_HECTARES` at one place to stay in that unit.

## Why it matters

A civilisation's own area word should only exist at the display edge
(`Complaints/132`). Here a Roman unit is the key of a material and a recipe
field, so every other civilisation's land is priced through it.

## What it would take

Rename the material to a hectare material and the field to
`land_hectare_years` (values divided by the iugerum in hectares), then drop
`IUGERUM_HECTARES` from the solver. This touches `data/production/`, the
solver and its report, and `sim/tests/test_price_solver_land.py`; it was left
because the price-book removal work owns those files.

## Done

The material is `hectare_land`, the recipe field `land_hectare_years` (each old value multiplied once by 0.2523, kept to eight decimals), and the tree nodes that consume land carry hectares. `IUGERUM_HECTARES` is removed from `sim/world/land.py`; `land_rent_hours_per_hectare` in the solver no longer converts. `data/prices.json` carries one book line for the renamed material, left for the price-book removal work.
