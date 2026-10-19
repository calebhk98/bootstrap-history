# Lime is burned only with coal, and there is no Roman concrete

**Status:** closed - wood-fired lime, pozzolana and Roman concrete exist and are wired into the dome, harbour, aqueduct and canal-lock nodes; the coal price and located-material freight are filed as 562 and 563

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

## Resolution

- `lime_wood_kg`, `pozzolana_kg` and `concrete_pozzolanic_kg` exist (`data/production/30_fuel_stone.json`).
- Wired to `concrete_pozzolanic_kg` with sourced masses (each node's `_internal` carries a `[BASIS: ...]`):
  `civ_dome_roman`, `sea_harbours_pozzolana`, `med_aqueducts_latrines`, and `tr_canal_lock` (`sea_canal_lock` is
  merged into it). The aqueduct's separate lime and stone are dropped, since the concrete contains them.
- The coal-below-firewood price was traced and is not a single wrong input; see Complaint 562.
- Pozzolana's 3x multiplier cannot be replaced by data alone: located materials are not freighted from their
  sites (Complaint 563). It is now labelled as a heuristic with `retire: Complaints/563`.
- Tests: `sim/tests/test_lime_wood_and_pozzolanic_concrete.py`.
