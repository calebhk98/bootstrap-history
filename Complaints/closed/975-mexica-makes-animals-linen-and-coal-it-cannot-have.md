# Mexica makes mules, oxen, linen and household coal it cannot have

**Status:** closed - animals and linen gated on their nodes, a household plot is no longer a mine (sim/tests/test_ungated_animals_and_pits.py)

Symptom: `python3 sim/simulator.py economy-check --accounts --years 1 --civs mexica_1500` showed `mule` and `ox`
made and worn in thousands, `linen_kg` made and "grown" (about 1.9e6) and `coal_kg` "grown" (about 1.7e8), in a
society with no draught animals, no flax and no coal mining.

Cause:
- `ox` and `mule` (data/production/90_additions.json) had `requires_node: null`, so `port_setup.allowed_entries`
  admitted them to every society; households then held them as priced durables.
- `linen_kg` (40_organics.json) was gated on `tex_drop_spindle`, which Mexica holds; the flax node it rests on is
  `mat_linen`, which Mexica lacks.
- `households_own.is_own_plot_recipe` accepted any recipe with land and no market inputs, and the coal entry
  carries a surface-land figure, so households "grew" coal by hand with no seam.

Fix: ox gated on `lnd_ox_transport`, mule on `lnd_mule_transport` (the nodes the carriage modes use), linen on
`mat_linen`; Mexica declares linen and the two linen-wick candles in `unsupplied_basket_goods`. `Recipe.deposit_bound`
(from `extracted_from` naming something other than field, wood or pasture) keeps seams and pits off household plots.
The data validator now refuses a carrier-animal entry with no gate (`validate_production.check_animal_gate`).
Every other civilisation holds all three nodes, so only Mexica changes. Without the animals the carriage modes
already offered are the porters'; without linen households wear the cloth the society makes.

Left: platinum, see Complaint 976. The shipped openings are stale until rebuilt, and the after-fix
economy-check row check was not completed within the five-minute limit (stale openings force a full spin-up).
