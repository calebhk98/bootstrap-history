"""Coin moved between two places of the home country pays carriage by its mass and the distance.

While the ledger listens to transfers (`transfer_listening`), each transfer between two actors that stand in different
places pays the carriers what hauling that mass of coin over the cheapest route costs; the payer pays it on top, to
`edge:freight`, so money is conserved. Payment within one place costs nothing, and credit (interest, a loan) moves no
coin. A party with no place (an edge standing for many people, a body of people, a firm, which has no tile of its own)
is charged nothing: there is no distance to price. Foreign settlement pays its own carriage (`coin_carriage_units`).
The module answers the ledger's `transfer_surcharge` point with `carriage_surcharge`."""
from typing import Any, Optional, Tuple

from sim.agents.api import edges

from . import rules
from .constants import CARRIAGE_CAUSE


class Carriage:
    """The surcharge on a transfer (needs: home_country, tile_known, tile_haul_cost, civilisation)."""

    def place_of(self, party) -> Optional[str]:
        """The tile a party stands on: a seat's purse at the home country's centre, another actor where its
        record places it; None for an edge or a party without a place."""
        if getattr(party, "stands_at_home", False):
            place = self.needs.home_country()["location"]
        else:
            locate = getattr(party, "location", None)
            place = locate() if callable(locate) else None
        return place if self.needs.tile_known[place] else None

    def carriage_surcharge(self, payer: Any, payee: Any, amount: float, purpose: Any) -> Optional[Tuple[str, float, str]]:
        """(edge, money, cause) the payer pays the carriers for moving `amount` of coin from its place to the payee's,
        or None when nothing is owed."""
        if amount <= 0.0 or rules.is_credit(purpose):
            return None
        if rules.abroad((payer, payee), self.needs.home_country()["id"]):
            return None
        origin, destination = self.place_of(payer), self.place_of(payee)
        if origin is None or destination is None or origin == destination:
            return None
        carriage = rules.carriage_money(amount, self.coin_kg_per_unit(), self.needs.tile_haul_cost(origin, destination))
        if carriage > 0.0:
            return edges.EDGE_FREIGHT, carriage, CARRIAGE_CAUSE
        return None
