# Material carriage charges one land mode for the whole route, even across the sea

**Status:** closed - material carriage prices the cheapest route leg by leg through the haul function foreign trade shares

Found closing 563. `material_carriage_per_tonne` (`sim/engine/economy_freight.py`) takes the distance of the cheapest
route over the modes held (`material_freight_distance_km`) and prices all of it with
`domestic_haul_money_per_tonne` (`sim/engine/domestic_haul.py`), which picks one domestic mode for the cargo class
and charges its rate over the whole distance. A route that is mostly sea is billed as if carted. Han's pozzolana
from the Campi Flegrei site, a route of many thousands of kilometres, costs thousands of times its site price per
kilogram in carriage; tracked minerals with a far nearest deposit are charged the same way.

Measure: `PYTHONPATH=. python3 -c "from sim.tests.harness import unopened_sim; s=unopened_sim(civ='han_china_100ad'); print(s.material_freight_distance_km('pozzolana_kg'), s.material_carriage_per_tonne('pozzolana_kg', 1.0))"`.

Why it matters (CLAUDE.md 4.5, 4.2): long-distance trade in bulk goods went by water because it was far cheaper; a
cart rate over a sea route makes every far material unaffordable and hides the coast-versus-inland pattern the
freight model exists to produce. Related: 561 (mode ratios), 541 (closed).

What it would take: price the route leg by leg with each leg's own mode (the route search already returns the legs
for foreign routes, `foreign_routes`), with handling at each change of mode; one function for domestic and foreign
hauls. Test: a material whose route is mostly sea costs, per tonne-km, near the sea rate plus handling, not the
cart rate.

## Resolution

`material_haul_route` (`sim/engine/domestic_haul.py`) finds the cheapest route from the nearest source tiles to the
tiles held over the modes held and the ways built, through `_haul_route` (`sim/engine/foreign_routes.py`), the same
function `_foreign_route` now calls: each leg at its own mode's money rate, the mode's dues at every change of mode.
`material_freight_cost_per_kg`, `material_freight_factor` and `material_carriage_per_tonne` take that route's cost, and
`domestic_cargo_cost_share` takes the route (interest and spoilage over its travel days, a herd's daily loss per leg's
mode). Where no way joins the source, one leg of the cargo's mode over the great-circle distance is priced by the same
leg pricing (`_unjoined_haul`). `Leg` and `Route` moved to `sim/engine/haul_route.py`. Routes are kept per prices,
flows and ways, so a repeat call is a lookup.

The complaint's measure command now gives Han pozzolana carriage well below the one-cart-rate figure; what remains is
the two overland gaps on the route (the Suez isthmus and the Myanmar crossing) at the cart rate over rough ground,
while the sea legs cost the sail rate plus one port handling. Norse pozzolana, tin and saltpetre fall by orders of
magnitude (the same command with `civ='norse_900ad'` and the material). The cart-versus-sail ratio itself is
Complaint 561. Test: `sim/tests/test_material_haul_legs.py`.
