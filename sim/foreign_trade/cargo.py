"""The year's cargo of the trader actors, kept as legs until the home market has cleared, then settled once.

A trader decides a cargo at the year's start against quotes and is booked at them. The partner's side is real money at once (the
foreign coin ledger and the route's carriers); the home side is whatever the agent economy's book gave the cargo, or the quote
where the book took none of it. Settling trues the trader's purse up from the booking to the result and closes the partner's
tally on what really crossed.
A leg is a plain dict kept in the module's world state (`cargo`, leg id -> leg), so a save carries it.

(needs: home_unit_price; sends PayActorFromEdge, PayEdgeFrom, NoteTraderMargin)"""
from typing import Any, Dict, List

from sim.agents.api import GOVERNMENT_PREFIX, edges
from sim.actors.api import NoteTraderMargin
from sim.ledger.api import PayActorFromEdge, PayEdgeFrom
from sim.refusal import Refusal

from . import rules
from .constants import SETTLEMENT


class Cargo:

    def cargo_legs(self) -> List[Dict[str, Any]]:
        """The legs noted since the last settlement, in a stable order."""
        return [leg for _id, leg in sorted(self.world.cargo.items())]

    def apply_note_cargo_leg(self, command: Any) -> None:
        """Note a cargo a trader shipped; the same trader, route and good in one year is one leg. `duty` is the part of
        `carriage` that is the destination state's tariff."""
        kind, partner = rules.cargo_kind(command.destination, command.source, command.home)
        leg_id = rules.cargo_leg_id(command.trader_id, partner, command.source, command.destination, command.material, kind)
        legs = self.world.cargo
        leg = legs.setdefault(leg_id, rules.blank_leg(leg_id, command.trader_id, kind, command.source, command.destination,
                                                      partner, command.material))
        leg["tonnes"] += command.tonnes
        leg["paid"] += command.paid
        leg["received"] += command.received
        leg["carriage"] += command.carriage
        leg["duty"] += command.duty

    def _pay_partner(self, partner: str, tonnes_signed: float, value: float) -> None:
        """Settle one side of a cargo with a partner in coin, and count it against the route's carriers."""
        per_coin = self.money_per_partner_coin(partner)
        if per_coin and value > 0.0:
            self.settle_flow(partner, tonnes_signed, value, per_coin)
        self.record_lift(partner, self.partner_facts(partner)["route"], tonnes_signed, 0.0)

    def apply_settle_trader_cargo(self, command: Any) -> None:
        """Settle every noted leg. `results` is what the book gave each leg that entered it ({leg id: {"tonnes", "money"}}); a
        leg it did not take is settled at its quote, as is every leg when `results` is None (no book)."""
        results = command.results or {}
        for leg in self.cargo_legs():
            taken_back, payments, delta = rules.leg_settlement(leg, results.get(leg["id"]))
            if taken_back is not None:
                rules.note_actor_trade(self.world.actor_trade, leg["partner"], leg["material"], taken_back, True)
            for partner, tonnes_signed, value in payments:
                self._pay_partner(partner, tonnes_signed, value)
            self._pay_duty(leg)
            self._true_up_trader(leg["trader"], delta)
        self.world.cargo = {}

    def _pay_duty(self, leg: Dict[str, Any]) -> None:
        """The tariff a cargo paid in its carriage reaches the treasury of the country it entered, if the cast holds one."""
        if leg.get("duty"):
            self.needs.send(PayActorFromEdge(edges.EDGE_FREIGHT, GOVERNMENT_PREFIX + leg["destination"], leg["duty"], "tax:tariff"))

    def _true_up_trader(self, trader_id: str, delta: float) -> None:
        """The trader's purse and margin follow what a cargo really made against what it was booked at."""
        if delta == 0.0:
            return
        if isinstance(self.needs.send(NoteTraderMargin(trader_id, delta)), Refusal):
            return   # no such trader in the cast
        if delta > 0.0:
            self.needs.send(PayActorFromEdge(edges.EDGE_MARKET, trader_id, delta, SETTLEMENT))
        else:
            self.needs.send(PayEdgeFrom(trader_id, edges.EDGE_MARKET, -delta, SETTLEMENT))

