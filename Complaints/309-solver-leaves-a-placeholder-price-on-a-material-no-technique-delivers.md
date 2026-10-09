# The solver leaves its starting guess as the price of a material no technique delivers

**Status:** partly - disposal sink services, a dump distance rule, per-material heap data and a glut found by the clearing search are built, but in the Rome solve wood_tar_kg prices at about 5e-20 again (test_solved_wood_tar_is_not_a_denormal fails), so the bound does not hold there

When no technique in a solve can be costed for a material (a recipe needing a heat nothing in the solve reaches, so every candidate fails the capability floor), `solve_round_update_prices` keeps the starting guess, and `compute_resolvable_materials` still calls the material resolvable. The guess is printed as a price. It was invisible while every solve held the mature techniques; a solve restricted to what a civilisation can reach shows it for cement, silicon carbide, cobalt and others (find them: materials in a solve's `resolvable_materials` with no entry in `chosen_recipe_by_material`). `priced_goods_table` now skips such a material in the held and reach tables and falls back, but the solver itself should not call it resolvable.

Related: a worthless joint by-product (`wood_tar_kg`) is damped toward zero and can underflow to a denormal; `economy_materials._generic_national_output_uncached` now guards the power, but a joint by-product with no demand wants a floor or an anchor in the solver. See `Complaints/38`, `Complaints/302`.

Related: 119.


Joint by-product floor: sim/engine/joint_floor.py lifts every output of a joint batch to a labelled share of the batch's standalone cost per kg, paid for by the outputs above it, so a by-product in glut (wood_tar_kg) no longer decays to a denormal. Measure: the solved price of wood_tar_kg for rome_100ad (was 4e-27 hours per kg, now above 1e-4; print it with the Rome solve in test_joint_byproduct_floor).

Owner decision (2026-10-02): a waste product can have a negative value (you pay to get rid of it); check whether the by-product floor is right before keeping it, so this is reopened.

Research done (2026-10-09): `Complaints/reports/negative-byproduct-value-research.md` recommends a disposal sink recipe (handling, haulage to a dump, land for the heap) whose cost bounds a by-product's price from below, replacing JOINT_BYPRODUCT_FLOOR_SHARE, and lists what the solver must change. Sources were read through search summaries only; check before quoting.
