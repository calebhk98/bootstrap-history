# Carried provisions may be divided out twice on a haul leg

**Status:** closed - provisions were divided out twice on searched legs; now counted once, at each leg's own share

Found closing 568. The route search's rates are already the mode's money per tonne-km over the share of lift left
after the carrier's own food. `_with_carried_provisions` (`sim/engine/foreign_routes.py`, now used by every haul
through `_haul_route`) appears to divide by that share again when it prices a leg, so a leg's cost is inflated by
one more factor of the lift lost to provisions. Checked only on Han's overland cart legs; it applies to every
foreign and domestic haul.

Measure: compare a single cart leg's money per tonne from `_haul_route` with `freight_cost.leg_money_per_tonne`
called once at the search rate for the same distance (no committed command prints both).

Why it matters (CLAUDE.md 4.5): every imported good's price and every material's carriage carry the error, most on
long land legs where provisions take the largest share of lift.

What it would take: trace where the provisions share enters the search rate and the leg price, keep it in exactly
one place, and add a test that a leg's money equals the mode's rate over the distance with provisions counted once.

## Resolution

It was a bug. `foreign_route_choice.choose_route` hands the route search rates already divided by the mode's
share of lift (the mean leg's share), and `_with_carried_provisions` then divided each found leg's cost by
its own share again. Fix (`sim/engine/foreign_routes.py`): `_haul_route` passes the base and searched rates,
and `_with_carried_provisions` replaces the share the rate already carried with the leg's own, so the food
is counted once. Domestic one-leg hauls pass no rates and are priced as before.

Measured on the default game's cart haul from `chad_08` (one leg, `_haul_route` at the quick-tier fixture):
the leg cost fell by the share it was divided by twice (about one eighth), and now equals the handling fee
plus the geography leg at the base rate over the leg's share. Sail legs were unchanged where the mean share
equalled the leg's share. Tests: `ProvisionsCountedOnce` in `sim/tests/test_material_haul_legs.py` and two in
`sim/tests/test_freight_provisions.py`.
