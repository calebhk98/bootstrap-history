"""Settling a haul's tolls and port dues: each due is paid to the treasury of whoever holds the tile it is levied at.

The route search prices the dues per tonne (`_freight_handling_costs`); this reads the found route against the
owner map when cargo is carried, so the holder at the time is paid and a transfer of a tile moves the revenue.
"""
from sim.agents.api import pay_dues, treasury_of
from sim.geography.api import dues_hours_per_tonne, route_dues_by_holder


def dues_money_per_tonne(dues_hours, wage):
    """{mode: money per tonne} of the modes that levy dues, the hours per tonne paid at the carrier's wage."""
    return {mode: hours * wage for mode, hours in dues_hours.items() if hours > 0.0}


def handling_money_per_tonne(dues_hours, wage, port_mode, port_handling_hours):
    """{mode: money per tonne} charged once per leg: each mode's dues, and port handling on top at `port_mode`."""
    costs = dues_money_per_tonne(dues_hours, wage)
    costs[port_mode] = costs.get(port_mode, 0.0) + port_handling_hours * wage
    return costs


class RouteDuesMixin:
    """Mixed into `Sim`."""

    def route_dues_per_tonne_by_mode(self):
        """{mode: home money per tonne} of tolls and port dues alone (the carriers' wage on the geography's hours)."""
        wage = self.labour.wage_per_hour(self.FREIGHT_DRIVER_WAGE_TRADE)
        return dues_money_per_tonne(dues_hours_per_tonne(self.world_map), wage)

    def route_dues_treasury(self, holder):
        """The account a country's or seat's dues are paid into."""
        return treasury_of(holder, self.state.seats, self.seat_party, self.actors)

    def route_dues_by_holder(self, route, tonnes):
        """{holder: money owed} for `tonnes` carried over a `Route`, by who holds each leg's starting tile now."""
        legs = [{"from": leg.origin, "mode": leg.mode} for leg in route.legs]
        return route_dues_by_holder(legs, self.route_dues_per_tonne_by_mode(), self.tile_owner, tonnes)

    def pay_route_dues(self, payer, route, tonnes, limit=None):
        """The payer pays each holder its dues for `tonnes` over the route, never more than `limit` in all;
        returns the money paid."""
        return pay_dues(payer, self.route_dues_by_holder(route, tonnes), self.route_dues_treasury, limit)
