# Carried provisions may be divided out twice on a haul leg

**Status:** open

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
