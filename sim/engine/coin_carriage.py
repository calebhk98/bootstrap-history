"""Coin moved between two places of the home country pays carriage by its mass and the distance.

While the engine listens (`Sim.coin_carriage_listening`), each transfer between two actors that stand in
different places pays the carriers what hauling that mass of coin over the cheapest route costs; the payer
pays it on top, to `edge:freight`, so money is conserved. Payment within one place costs nothing, and credit
(interest, a loan) moves no coin. A party with no place (an edge standing for many people, a body of people, a
firm, which has no tile of its own) is charged nothing: there is no distance to price. Foreign settlement pays
its own carriage (`coin_carriage_units`, `coin_hoard.py`).
"""
from typing import Any, Optional

from sim.agents.api import edges, ledger
from sim.geography.api import route as route_over_tiles
from sim.geography.api import usable_modes as usable_route_modes

from .foreign_routes import route_from_geography

CARRIAGE_CAUSE = "coin carriage"
CREDIT_PURPOSES = frozenset({"interest", "loan", "loan repayment"})  # claims on a debtor: no coin changes hands


def carriage_money(amount: float, kg_per_unit: float, money_per_tonne: float) -> float:
    """Carriage on `amount` of coin: its mass times the haul's price per tonne, never more than is moved."""
    tonnes = max(0.0, amount) * kg_per_unit / 1000.0
    return min(max(0.0, amount), tonnes * max(0.0, money_per_tonne))


def is_credit(purpose: Any) -> bool:
    labels = purpose.keys() if hasattr(purpose, "keys") else (purpose,)
    return all(label in CREDIT_PURPOSES for label in labels)


class CoinCarriageMixin:
    """Mixed into `Sim`."""

    def coin_carriage_listening(self):
        """Context in which every transfer between actors may pay carriage."""
        return ledger.listening(self.charge_coin_carriage)

    def place_of(self, actor) -> Optional[str]:
        """The tile an actor stands on: the founder's household at the home country's centre, another actor
        where its record places it; None for an edge or an actor without a place."""
        if actor is self.state.household:
            home = self.actors.state.countries.get(self.actors.state.home_country)
            place = None if home is None else home.location
        else:
            locate = getattr(actor, "location", None)
            place = locate() if callable(locate) else None
        return place if place in self.world_map.tiles else None

    def home_carriage_per_tonne(self, origin: str, destination: str) -> float:
        """Home money to haul a tonne over the cheapest route between two tiles; nothing where none joins them.
        Remembered for the year."""
        cache = self.__dict__.setdefault("_home_carriage_cache", {})
        year = self.state.scenario.year
        if cache.get("year") != year:
            cache.clear()
            cache["year"] = year
        key = (origin, destination)
        if key not in cache:
            home_techs = frozenset(self.state.projects.done)
            mode_costs = self._freight_mode_costs(0.0)
            modes = [mode for mode in usable_route_modes((home_techs,), self.world_map) if mode in mode_costs]
            found = route_over_tiles([origin], [destination], modes, mode_costs=mode_costs,
                                     handling_costs=self._freight_handling_costs(), held_nodes=home_techs,
                                     world_map=self.world_map)
            cache[key] = 0.0 if found is None else self._with_carried_provisions(
                route_from_geography(found)).cost_per_tonne
        return cache[key]

    def charge_coin_carriage(self, payer, payee, amount, purpose):
        """The payer pays the carriers for moving `amount` of coin from its place to the payee's."""
        if amount <= 0.0 or is_credit(purpose):
            return
        home = self.actors.state.home_country
        for party in (payer, payee):
            record = getattr(party, "record", None)
            if record is not None and record.country not in (None, home):
                return
        origin, destination = self.place_of(payer), self.place_of(payee)
        if origin is None or destination is None or origin == destination:
            return
        carriage = carriage_money(amount, self.coin_kg_per_unit(), self.home_carriage_per_tonne(origin, destination))
        if carriage > 0.0:
            ledger.transfer(payer, self.edge(edges.EDGE_FREIGHT), carriage, CARRIAGE_CAUSE)
