# The solver leaves its starting guess as the price of a material no technique delivers

**Status:** partly - no material keeps the starting guess: one no technique in reach makes is dropped with its dependents (`sim/solve_prices_reach.py`, test price_solver_unreachable_material); the joint by-product floor (the `wood_tar_kg` underflow) remains

When no technique in a solve can be costed for a material (a recipe needing a heat nothing in the solve reaches, so every candidate fails the capability floor), `solve_round_update_prices` keeps the starting guess, and `compute_resolvable_materials` still calls the material resolvable. The guess is printed as a price. It was invisible while every solve held the mature techniques; a solve restricted to what a civilisation can reach shows it for cement, silicon carbide, cobalt and others (find them: materials in a solve's `resolvable_materials` with no entry in `chosen_recipe_by_material`). `priced_goods_table` now skips such a material in the held and reach tables and falls back, but the solver itself should not call it resolvable.

Related: a worthless joint by-product (`wood_tar_kg`) is damped toward zero and can underflow to a denormal; `economy_materials._generic_national_output_uncached` now guards the power, but a joint by-product with no demand wants a floor or an anchor in the solver. See `Complaints/38`, `Complaints/302`.
