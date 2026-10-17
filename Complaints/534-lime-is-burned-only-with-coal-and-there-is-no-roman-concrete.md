# Lime is burned only with coal, and there is no Roman concrete

**Status:** partly done. Data added: `lime_wood_kg` (firewood-fired lime, 1530 kg firewood per tonne from the calcination enthalpy at 20% kiln efficiency), `pozzolana_kg` (extracted; sited by the `pozzolana` located material at Campi Flegrei/Vesuvius, Alban Hills, Santorini, Eifel), `concrete_pozzolanic_kg` (gated on `mat_pozzolana`; Vitruvius proportions), wired into `civ_dome_roman`. Tests: `sim/tests/test_lime_wood_and_pozzolanic_concrete.py`. Still open: wire harbour, aqueduct and canal-lock nodes (`sea_harbours_pozzolana`, `med_aqueducts_latrines`) to concrete once their masses are sourced; check why coal undercuts firewood at the Rome opening (command above); the 3x pozzolana cost multiplier is a freight stand-in.

Reference (an outside table of ancient supply chains, not code-aware): masons used dressed stone,
bricks, lime from lime kilns, and pozzolana (volcanic ash) for hydraulic concrete in aqueducts,
harbours and vaults.

## What the data does

- `lime_kg` (`data/production/30_fuel_stone.json`) has one recipe, limestone plus `coal_kg`. There is
  no wood- or charcoal-fired kiln, although ancient lime was burned with wood. Every mortar and
  wall (`mortar_kg`, `brick_wall_m3`, `stone_wall_m3`) depends on coal.
- At the Rome opening coal is cheaper per kilogram than firewood:

      python3 -c "from sim.tests.harness import sim; s=sim(civ='rome_100ad'); print({g: s._material_price_per_kg(g) for g in ('coal_kg','firewood_kg','lime_kg')})"

  Whether that coal price is itself right was not checked here.
- No pozzolana good and no lime-pozzolana concrete; the only concrete is `concrete_reinforced_kg`.

## What it would take

- A wood-fired lime recipe (fuel from the stoichiometric heat of calcination plus kiln losses),
  and coal kept as a second technique so the cheaper one wins.
- `pozzolana_kg` as a deposit-bound extracted good and a hydraulic concrete recipe gated on its node.
- Check why coal undercuts firewood at the Rome opening, and file it if it is wrong.
