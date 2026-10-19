"""Settling a haul's tolls and port dues: each due is paid to the treasury of whoever holds the tile it is levied at.

The route search prices the dues per tonne (`_freight_handling_costs`); this reads the found route against the
owner map when cargo is carried, so the holder at the time is paid and a transfer of a tile moves the revenue.
"""
from sim.agents.api import ledger
from sim.geography.api import dues_hours_per_tonne, route_dues_levied

DUES_CAUSE = "route dues"


class RouteDuesMixin:
    """Mixed into `Sim`."""

    def route_dues_per_tonne_by_mode(self):
        """{mode: home money per tonne} of tolls and port dues alone (the carriers' wage on the geography's hours)."""
        wage = self.labour.wage_per_hour(self.FREIGHT_DRIVER_WAGE_TRADE)
        return {mode: hours * wage for mode, hours in dues_hours_per_tonne(self.world_map).items() if hours > 0.0}

    def route_dues_treasury(self, holder):
        """The account a country's or seat's dues are paid into."""
        if holder in self.state.seats:
            return self.seat_party(holder)
        return self.actors.government_of(holder) or self.actors.ensure_government(str(holder))

    def route_dues_by_holder(self, route, tonnes):
        """{holder: money owed} for `tonnes` carried over a `Route`, by who holds each leg's starting tile now."""
        legs = [{"from": leg.origin, "mode": leg.mode} for leg in route.legs]
        owed = {}
        for due in route_dues_levied(legs, self.route_dues_per_tonne_by_mode(), self.tile_owner):
            owed[due["holder"]] = owed.get(due["holder"], 0.0) + due["per_tonne"] * tonnes
        return owed

    def pay_route_dues(self, payer, route, tonnes, limit=None):
        """The payer pays each holder its dues for `tonnes` over the route, never more than `limit` in all;
        returns the money paid."""
        owed = self.route_dues_by_holder(route, tonnes)
        total = sum(owed.values())
        scale = 1.0 if limit is None or total <= limit else max(0.0, limit) / total
        paid = 0.0
        for holder in sorted(owed):
            amount = owed[holder] * scale
            if amount > 0.0:
                ledger.transfer(payer, self.route_dues_treasury(holder), amount, DUES_CAUSE)
                paid += amount
        return paid
