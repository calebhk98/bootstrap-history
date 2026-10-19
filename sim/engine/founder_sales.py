"""The founder sells: a built concern to another actor through the exchange, farmland back to the land market."""
from sim.agents.api import CommandRejected, exchange_sale

from .agents_port import SimWorld
from .units_prose import area_text
from sim.agents.api import edges


class FounderSalesMixin:

    def _concern_sale_setup(self, node_id):
        """(seller party, candidate buyers, find_actor, world) for selling a concern, or (None, why not)."""
        projects = self.state.projects
        if node_id not in projects.operating or node_id in projects.granted:
            return None, "you are not running %s, so there is nothing to sell" % node_id
        world = SimWorld(self)
        party = self.seat_party(self.state.acting_seat, {node_id: world.concern_margin(node_id)})

        def find_actor(actor_id):
            return party if actor_id == party.actor_id else self.actors.get(actor_id)

        buyers = [actor for actor in self.actors.of_kind("firm") + self.actors.of_kind("player")
                  if getattr(actor.record, "exited_year", None) is None]
        return (party, buyers, find_actor, world), None

    def quote_concern_sale(self, node_id):
        """What `sell_concern` would do now, without doing it: {"ok", "buyer", "price"} or {"ok": False, "error"}."""
        setup, error = self._concern_sale_setup(node_id)
        if setup is None:
            return {"ok": False, "error": error}
        party, buyers, _find_actor, world = setup
        try:
            terms = exchange_sale.sale_terms(party, node_id, buyers, world)
        except CommandRejected as reason:
            return {"ok": False, "error": str(reason)}
        return {"ok": True, "concern": node_id, "buyer": terms["buyer"].actor_id, "price": round(terms["price"], 1),
                "capital": round(self.household.capital, 1)}

    def sell_concern(self, node_id):
        """Sell a concern you run to the actor the exchange picks, at the price it sets. {"ok", ...}."""
        projects = self.state.projects
        setup, error = self._concern_sale_setup(node_id)
        if setup is None:
            return {"ok": False, "error": error}
        party, buyers, find_actor, world = setup
        try:
            sale = exchange_sale.sell_concern(party, node_id, buyers, find_actor, world)
        except CommandRejected as reason:
            return {"ok": False, "error": str(reason)}
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
            return {"ok": False, "error": "you own %s of farmland, not %s" % (area_text(owned, self, digits=1),
                                                                       area_text(hectares, self, digits=1))}
        price = hectares * self.farm_price_per_hectare()
        holdings.farm_hectares = owned - hectares
        self.receive_from_edge(edges.EDGE_LANDOWNERS, price, "farmland sold")
        return {"ok": True, "sold_farm_hectares": hectares, "price": round(price, 1),
                "farm_hectares": round(holdings.farm_hectares, 1), "capital": round(self.household.capital, 1)}
