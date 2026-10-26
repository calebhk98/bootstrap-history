"""Coin is metal: what a purse of it weighs, what keeping that weight costs, and what carrying it costs.

The mass is the money held times the metal in one coin (the civilisation's coin standard). Keeping it costs guards'
hours by the tonne, priced at the unskilled hour like every other labour cost; carrying it over a route is priced by
the tonne through the route's freight. Any actor holding money pays the keeping cost, a foreign one at its own
country's pay."""
from sim.agents.api import edges
from sim.labour.api import wage_provider
from sim.ledger.api import PayEdgeFrom
from sim.world import coin_metal

from . import rules
from .constants import COIN_GUARD_HOURS_PER_TONNE_YEAR, KEEPING_CAUSE, KEEPING_PAY_TRADE


class Keeping:
    """The views of the hoard and its keeping cost, and the command `ChargeKeeping` (needs: civilisation,
    money_per_labour_hour, acting_balance, credit_limit, partner_coin_standard, partner_route_cost, legacy_actor_registry,
    legacy_agent_world; sends PayEdgeFrom)."""

    def coin_kg_per_unit(self):
        return wage_provider.coin_standard(self.needs.civilisation())["kg_per_unit"]

    def coin_keeping_cost(self, money):
        """Yearly cost of keeping `money` as coin of the home standard under guard."""
        return coin_metal.keeping_cost_per_year(
            money, self.coin_kg_per_unit(), COIN_GUARD_HOURS_PER_TONNE_YEAR, self.needs.money_per_labour_hour())

    def coin_hoard(self):
        """The money held as physical coin: its metal, mass and the yearly cost of keeping it."""
        money = self.needs.acting_balance()
        return rules.hoard(wage_provider.coin_standard(self.needs.civilisation())["material"], money,
                           self.coin_kg_per_unit(), self.coin_keeping_cost(money))

    def coin_hoard_report(self):
        """`coin_hoard` rounded for a screen."""
        return rules.hoard_report(self.coin_hoard())

    def coin_keeping_due(self, revenue, upkeep, living_cost, mine_cost):
        """(what keeping the household's coin under guard costs this year, what the household pays of it)."""
        capital, credit_limit = self.needs.acting_balance(), self.needs.credit_limit()
        return rules.keeping_due(self.coin_hoard()["keeping_cost_per_year"], capital, credit_limit, revenue, upkeep,
                                 living_cost, mine_cost)

    def coin_carriage_units(self, civilization_id, units, home_money_per_partner_coin):
        """Partner coin units the carriers take to move `units` of the partner's coin over the route, by the coin's
        mass; never more than is moved. Nothing is charged where no route is known."""
        kg_per_unit = self.needs.partner_coin_standard[civilization_id]["kg_per_unit"]
        per_tonne = self.needs.partner_route_cost[civilization_id]
        return coin_metal.carriage_units(units, kg_per_unit, 0.0 if per_tonne is None else per_tonne,
                                         home_money_per_partner_coin)

    def charge_keeping(self, command):
        """Every actor in business that holds money (a state, a firm) pays to keep it as coin. A foreign country's
        actor pays at its country's own pay level (its own labour markets) to its own country's guards."""
        registry, world = self.needs.legacy_actor_registry(), self.needs.legacy_agent_world()
        home_pay = max(1e-9, world.pay_per_person_year(KEEPING_PAY_TRADE))
        for actor_id, actor in sorted(registry.actors.items()):  # id order, as a loaded game wraps them
            record = actor.record
            if record.exited_year is not None or actor.money <= 0.0 or record.stratum:
                continue
            country = record.country
            at_home = country in (None, registry.state.home_country)
            cost = self.coin_keeping_cost(actor.money)
            if not at_home:
                cost *= registry.world_for(actor, world).pay_per_person_year(KEEPING_PAY_TRADE) / home_pay
            if cost > 0.0:
                guards = edges.EDGE_COIN_GUARDS if at_home else "%s:%s" % (edges.EDGE_COIN_GUARDS, country)
                self.needs.send(PayEdgeFrom(actor_id, guards, cost, KEEPING_CAUSE))
