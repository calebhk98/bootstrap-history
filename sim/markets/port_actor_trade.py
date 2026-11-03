"""Firms', states' and traders' sales and purchases through the agent economy's year. Part of the port.

The year's notes are plain dicts kept in the agent economy's stored record (`sales`, `purchases`), so a save carries them;
port_actors.py turns them into orders and settles them. This object notes them, posts them when the year runs and turns what
they fetched back into the actors' coin."""
from sim.actors import api as actors_api
from sim.economy import api as economy_api
from sim.ledger.api import UNPAID_CHARGE_KIND, PayExchange, ReceiveFromExchange
from sim.reporting.api import RecordEvent
from sim.prices.api import prices as price_solver
from .unit_mass import tonnes_per_unit

from . import port_actors


class ActorTrade:

    def __init__(self, world, agent, seats):
        self._world = world
        self._agent = agent
        self._seats = seats
        # note_sale's lookup of the year's sales: [the list indexed, its length when indexed, {(seller, material): sale}].
        # It checks itself against the stored list on each note and rebuilds from it, so it is a function of the record and is not saved.
        self._sale_index = [None, 0, {}]

    def note_sale(self, seller, material, tonnes, from_concerns):
        port_actors.note_sale(self._agent.stored.setdefault("sales", []), seller, material, tonnes, from_concerns,
                              self._sale_index)

    def forget_index(self):
        """The notes were renamed in place, so the lookup no longer matches them."""
        self._sale_index = [None, 0, {}]

    def note_purchase(self, buyer, commodity, tonnes, budget):
        port_actors.note_purchase(self._agent.stored.setdefault("purchases", []), buyer, commodity, tonnes, budget)

    def forget_orders(self, actor_id):
        stored = self._agent.stored
        for kind, key in (("sales", "seller"), ("purchases", "buyer")):
            if kind in stored:
                kept = [order for order in stored[kind] if order[key] != actor_id]
                if len(kept) != len(stored[kind]):   # a list nothing left keeps its identity, and its index
                    stored[kind] = kept

    def held_units(self, buyer, material):
        return port_actors.held_units(self._agent.economy(), buyer, material)

    def fleet_goods(self, buyer):
        economy = self._agent.economy()
        production = price_solver.default_production_entries()
        specs = economy_api.good_specs(economy)
        tile = self._agent.actor_tile(buyer)
        candidates = [good for good in sorted(production) if good in economy_api.recipes_of(economy) and good in specs
                      and economy_api.recipe_allowed_at(economy, good, tile)]
        return port_actors.fleet_goods(production, candidates, lambda good: specs[good].service_life_years,
                                       lambda good: self.held_units(buyer, good))

    def post_orders(self, orders):
        """Put the year's noted sales and purchases of the actors in the book as orders; (the sales and the purchases
        that entered, as dicts)."""
        world, agent = self._world, self._agent
        economy = agent.economy()
        known = world.scenario.actors.actors
        stored = agent.stored
        sales = [sale for sale in stored.pop("sales", []) if sale["seller"] in known]
        purchases = [purchase for purchase in stored.pop("purchases", []) if purchase["buyer"] in known]
        view = economy.view()

        def reservation(seller, node_id, material, tile):
            return self._seats.reservation(node_id, material, tile, view, seller)

        moves, sale_orders = port_actors.sale_orders(economy, sales, tonnes_per_unit, agent.actor_tile, reservation)
        coin = economy_api.coin_per_unit(economy)
        purchase_orders, funding = port_actors.purchase_orders(
            economy, purchases, tonnes_per_unit, agent.actor_tile, world.economy.materials_in, coin)
        economy_api.move_goods(economy, moves)
        purchase_orders, funding, refused = port_actors.keep_paid_purchases(
            purchase_orders, funding, lambda buyer, coin_spent: world.send(PayExchange(buyer, coin_spent, "market purchases")))
        for buyer, coin_spent, refusal in refused:   # a purchase the buyer cannot pay for is not bid for
            world.send(RecordEvent.of(UNPAID_CHARGE_KIND, "%s could not pay for its market purchases: %s" % (buyer, refusal),
                                      actor=buyer, amount=coin_spent, purpose="market purchases", cause=refusal.cause))
        unfunded = {buyer for buyer, _coin, _refusal in refused} - {buyer for buyer, _coin, _units in funding}
        purchases = [purchase for purchase in purchases if purchase["buyer"] not in unfunded]   # no account was funded for them
        port_actors.fund(economy, funding)
        orders.update(sale_orders)
        orders.update(purchase_orders)
        return sales, purchases

    def settle(self, sales, purchases):
        """What the actors' sales fetched and their budgets left over turn back into their coin; the goods unsold go
        back out. Bought capital assets stay with their buyer and materials are used up."""
        economy = self._agent.economy()
        proceeds, refunds, delivered = port_actors.close(economy, sales, purchases)
        actors_api.keep_deliveries(self._world.scenario.actors.actors, delivered, tonnes_per_unit)   # goods a buyer that keeps its purchases bought join its stores, in tonnes
        coin = economy_api.coin_per_unit(economy)
        for amounts, label in ((proceeds, "market sales"), (refunds, "market purchases returned")):
            for actor_id, units in sorted(amounts.items()):
                self._world.send(ReceiveFromExchange(actor_id, units * coin, label))
