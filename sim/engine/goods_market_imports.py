"""How much of a good a trading partner can bring in a year.

A partner sells no more than it makes and holds, and the route's carriers lift no more than their lift
(foreign_payments.py); the home market's own output curves say nothing about either. What households and
the founder have already bought of the good this year comes off what is left."""
import math

HOME_SELLER = "home"


def import_tonnes_left(partner_supply_tonnes, lift_left_tonnes, bought_tonnes):
    """Tonnes of a good still to be had from a partner this year."""
    return max(0.0, min(partner_supply_tonnes, lift_left_tonnes) - bought_tonnes)


class GoodsImports:
    """Mixin of `GoodsOffers`: reads of what a partner can bring."""

    def import_tonnes_available(self, material, partner=None):
        """Tonnes a year to be had of a material from the partner that sells it (the named one, else
        the cheapest seller in reach); None when the home society is its seller or no one is."""
        sim = self._sim
        partner = partner or self.offered_by(material)
        if partner is None or partner == HOME_SELLER:
            return None
        route = self._route_from(partner)
        lift_in = sim.foreign_lift_left_tonnes(partner, route)[0] if route is not None else 0.0
        supply = sim.foreign_supply_tonnes(partner, material)
        bought = self.bought_tonnes(sim._material_tag(material)[0])
        left = import_tonnes_left(supply, lift_in, bought)
        return left if math.isfinite(left) else math.inf
