"""The founder sells: a built concern to another actor through the exchange, farmland back to the land market."""
from sim.agents.api import CommandRejected, HouseholdParty, exchange_sale

from .agents_port import SimWorld
from sim.agents.api import edges


class FounderSalesMixin:

    def sell_concern(self, node_id):
        """Sell a concern you run to the actor the exchange picks, at the price it sets. {"ok", ...}."""
        projects = self.state.projects
        if node_id not in projects.operating or node_id in projects.granted:
            return {"ok": False, "error": "you are not running %s, so there is nothing to sell" % node_id}
        world = SimWorld(self)
        party = HouseholdParty(self.household, {node_id: world.concern_margin(node_id)})

        def find_actor(actor_id):
            return party if actor_id == party.actor_id else self.actors.get(actor_id)

        buyers = [actor for actor in self.actors.of_kind("firm") + self.actors.of_kind("player")
                  if getattr(actor.record, "exited_year", None) is None]
        try:
            sale = exchange_sale.sell_concern(party, node_id, buyers, find_actor, world)
        except CommandRejected as reason:
            return {"ok": False, "error": str(reason)}
        projects.mothballed.discard(node_id)
        self.clear_closure(node_id)
        return {"ok": True, "sold": node_id, "buyer": sale["buyer"], "price": round(sale["price"], 1),
                "capital": round(self.household.capital, 1)}

    def sell_farm(self, hectares):
        """Sell farmland back to the land market at what `buy farm` charges per hectare, nothing taken as a fee."""
        hectares = float(hectares)
        economy = self.state.economy
        holdings = self.state.holdings
        owned = getattr(holdings, "farm_hectares", 0.0) or 0.0
        if hectares <= 0.0:
            return {"ok": False, "error": "hectares must be greater than zero"}
        if hectares > owned + 1e-9:
            return {"ok": False, "error": "you own %.1f hectares of farmland, not %.1f" % (owned, hectares)}
        price = hectares * self.farm_price_per_hectare()
        holdings.farm_hectares = owned - hectares
        self.receive_from_edge(edges.EDGE_LANDOWNERS, price, "farmland sold")
        return {"ok": True, "sold_farm_hectares": hectares, "price": round(price, 1),
                "farm_hectares": round(holdings.farm_hectares, 1), "capital": round(self.household.capital, 1)}
