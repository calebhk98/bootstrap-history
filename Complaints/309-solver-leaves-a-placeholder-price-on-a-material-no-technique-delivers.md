# The solver leaves its starting guess as the price of a material no technique delivers

**Status:** partly - reopened by owner decision (2026-10-02): the by-product floor (`sim/joint_floor.py`, JOINT_BYPRODUCT_FLOOR_SHARE) keeps every joint output above zero, but a waste product may cost money to dispose of; decide whether a negative value is the right model

When no technique in a solve can be costed for a material (a recipe needing a heat nothing in the solve reaches, so every candidate fails the capability floor), `solve_round_update_prices` keeps the starting guess, and `compute_resolvable_materials` still calls the material resolvable. The guess is printed as a price. It was invisible while every solve held the mature techniques; a solve restricted to what a civilisation can reach shows it for cement, silicon carbide, cobalt and others (find them: materials in a solve's `resolvable_materials` with no entry in `chosen_recipe_by_material`). `priced_goods_table` now skips such a material in the held and reach tables and falls back, but the solver itself should not call it resolvable.

Related: a worthless joint by-product (`wood_tar_kg`) is damped toward zero and can underflow to a denormal; `economy_materials._generic_national_output_uncached` now guards the power, but a joint by-product with no demand wants a floor or an anchor in the solver. See `Complaints/38`, `Complaints/302`.

Related: 119.


Joint by-product floor: sim/joint_floor.py lifts every output of a joint batch to a labelled share of the batch's standalone cost per kg, paid for by the outputs above it, so a by-product in glut (wood_tar_kg) no longer decays to a denormal. Measure: the solved price of wood_tar_kg for rome_100ad (was 4e-27 hours per kg, now above 1e-4; print it with the Rome solve in test_joint_byproduct_floor).

Owner decision (2026-10-02): a waste product can have a negative value (you pay to get rid of it); check whether the by-product floor is right before keeping it, so this is reopened.
