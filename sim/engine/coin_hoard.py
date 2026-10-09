"""Coin is metal: what a purse of it weighs, what keeping that weight costs, and what carrying it costs.

The mass is the money held times the metal in one coin (the civilisation's coin standard). Keeping it costs guards'
hours by the tonne, priced at the unskilled hour like every other labour cost; carrying it over a route is
priced by the tonne through the route's freight. Any actor holding money pays the keeping cost, a foreign one at its own country's pay.
"""
from sim.constants import declare

from sim.labour.api import wage_provider

from .data import load_civ
from sim.agents.api import edges, ledger

COIN_GUARD_HOURS_PER_TONNE_YEAR = declare(
    "COIN_GUARD_HOURS_PER_TONNE_YEAR", 60.0, kind="temporary_heuristic",
    unit="labour hours per tonne of coin per year", source=None, confidence="D",
    why="Watch-keeping and strongroom upkeep for a hoard, by its mass. Stands in for a vault built "
        "from stone, doors and a guard roster (a vault has no model yet), and is not measured. "
        "The household's purse is charged it each year.")

KEEPING_PAY_TRADE = "labourer"  # the pay that scales a foreign country's guards against the home guards
KEEPING_CAUSE = edges.EDGE_COIN_GUARDS  # paid to the guards, people in the economy
KEEPING_BASIS = ("guard hours per tonne of coin per year, a labelled heuristic "
                 "(COIN_GUARD_HOURS_PER_TONNE_YEAR), at the unskilled hour")


class CoinHoardMixin:
    """Mixed into `Sim`."""

    def coin_kg_per_unit(self):
        return wage_provider.coin_standard(self.civ)["kg_per_unit"]

    def coin_keeping_cost_per_year(self, money):
        """Yearly cost of keeping `money` as coin of the home standard under guard."""
        tonnes = max(0.0, money) * self.coin_kg_per_unit() / 1000.0
        return tonnes * COIN_GUARD_HOURS_PER_TONNE_YEAR * self.labour.money_per_labour_hour()

    def coin_hoard(self):
        """The money held as physical coin: its metal, mass and the yearly cost of keeping it."""
        tonnes = max(0.0, self.capital) * self.coin_kg_per_unit() / 1000.0
        return {"metal": wage_provider.coin_standard(self.civ)["material"],
                "tonnes": tonnes,
                "keeping_cost_per_year": self.coin_keeping_cost_per_year(self.capital),
                "basis": KEEPING_BASIS}

    def charge_actors_for_keeping_coin(self):
        """Every actor in business that holds money (a state, a firm) pays to keep it as coin. The founder's
        household is charged in its own money step. A foreign country's actor pays at its country's pay level
        (the scope's labelled rescale, Complaint 407) to its own country's guards."""
        from .agents_port import SimWorld
        world = SimWorld(self)
        home_pay = max(1e-9, world.pay_per_person_year(KEEPING_PAY_TRADE))
        for actor in self.actors.actors.values():
            record = actor.record
            if record.exited_year is not None or record.money <= 0.0 or record.stratum:
                continue
            country = record.country
            at_home = country in (None, self.actors.state.home_country)
            cost = self.coin_keeping_cost_per_year(record.money)
            if not at_home:
                cost *= self.actors.world_for(actor, world).pay_per_person_year(KEEPING_PAY_TRADE) / home_pay
            if cost > 0.0:
                guards = edges.EDGE_COIN_GUARDS if at_home else "%s:%s" % (edges.EDGE_COIN_GUARDS, country)
                ledger.transfer(actor, self.edge(guards), cost, KEEPING_CAUSE)

    def _coin_carriage_money_per_tonne(self, civilization_id):
        """Home money to carry a tonne over the route to a partner; nothing where no route is known."""
        route = self._foreign_economy_facts(civilization_id)["route"]
        return 0.0 if route is None else route.cost_per_tonne

    def coin_carriage_units(self, civilization_id, units, home_money_per_partner_coin):
        """Partner coin units the carriers take to move `units` of the partner's coin over the route, by
        the coin's mass; never more than is moved."""
        kg_per_unit = load_civ(civilization_id)["coin_standard"]["kg_per_unit"]
        cost = self._coin_carriage_money_per_tonne(civilization_id) * units * kg_per_unit / 1000.0
        return min(units, cost / home_money_per_partner_coin)

    def coin_hoard_report(self):
        """`coin_hoard` rounded for a screen."""
        hoard = self.coin_hoard()
        return {"metal": hoard["metal"], "tonnes": round(hoard["tonnes"], 3),
                "keeping_cost_per_year": round(hoard["keeping_cost_per_year"], 1),
                "basis": hoard["basis"]}
