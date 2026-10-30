"""Settling a haul's tolls and port dues: each due is paid to the treasury of whoever holds the tile it is levied at.

The route search prices the dues per tonne (`freight_handling_costs`); this reads the found route against the owner map
when cargo is carried, so the holder at the time is paid and a transfer of a tile moves the revenue."""
from sim.agents.api import DUES_CAUSE
from sim.geography.api import route_dues_by_holder
from sim.ledger.api import PayActor

from . import rules
from .constants import FREIGHT_DRIVER_WAGE_TRADE


class Dues:
    """Needs: carriage_facts, wage, tile_owner, holder_treasury; sends PayActor."""

    def route_dues_per_tonne_by_mode(self):
        """{mode: home money per tonne} of tolls and port dues alone (the carriers' wage on the geography's hours)."""
        wage = self.needs.wage[FREIGHT_DRIVER_WAGE_TRADE]
        return rules.dues_money_per_tonne(self.needs.carriage_facts()["dues_hours_per_tonne"], wage)

    def route_dues_by_holder(self, route, tonnes):
        """{holder: money owed} for `tonnes` carried over a `Route`, by who holds each leg's starting tile now."""
        legs = [{"from": leg.origin, "mode": leg.mode} for leg in route.legs]
        return route_dues_by_holder(legs, self.route_dues_per_tonne_by_mode(), lambda tile: self.needs.tile_owner[tile], tonnes)

    def pay_route_dues(self, command):
        """The payer pays each holder its dues for the tonnes over the route, never more than the command's limit in
        all; answers the money paid."""
        paid = 0.0
        for holder, amount in rules.dues_payments(self.route_dues_by_holder(command.route, command.tonnes), command.limit):
            self.needs.send(PayActor(command.payer, self.needs.holder_treasury[holder], amount, DUES_CAUSE))
            paid += amount
        return paid
