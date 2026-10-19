# Material carriage charges one land mode for the whole route, even across the sea

**Status:** open

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
