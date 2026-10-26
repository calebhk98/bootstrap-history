"""The farmland the acting seat holds: what it is worth, buying it and selling it back.

The holding itself (hectares, granary stock, last harvest) is still a section of the engine's household state that
demography and the farm workforce write; it is read and written here through `legacy_farm_holdings`."""
from sim.agents.api import edges
from sim.ledger.api import PayEdge, ReceiveFromEdge
from sim.refusal import Refusal

from . import rules
from .constants import FARM_LABOUR_HOURS_PER_HA


class Farm:

    def farm_holdings(self):
        """{hectares: farmland held, or None before a farm; stock_kg: the granary}."""
        holdings = self.needs.legacy_farm_holdings()
        return {"hectares": holdings.farm_hectares, "stock_kg": holdings.farm_stock_kg}

    def farm_land_price(self):
        """What one hectare of farmland costs now."""
        return FARM_LABOUR_HOURS_PER_HA * self.needs.money_per_labour_hour() * self.needs.price_index()

    def invest_farm(self, command):
        hectares = float(command.hectares)
        cost = hectares * self.farm_land_price()
        cause = rules.purchase_refusal(hectares, cost, self.needs.acting_balance())
        if cause == "not_positive":
            return Refusal(cause, "hectares must be greater than zero")
        if cause:
            return Refusal(cause, "cannot pay %.6g for %.6g hectares of farmland" % (cost, hectares))
        self.needs.send(PayEdge(edges.EDGE_LANDOWNERS, cost, "farmland bought"))
        holdings = self.needs.legacy_farm_holdings()
        holdings.farm_hectares = (getattr(holdings, "farm_hectares", 0.0) or 0.0) + hectares
        return hectares

    def sell_farm(self, command):
        hectares = float(command.hectares)
        holdings = self.needs.legacy_farm_holdings()
        owned = getattr(holdings, "farm_hectares", 0.0) or 0.0
        cause = rules.sale_refusal(hectares, owned)
        if cause == "not_positive":
            return Refusal(cause, "hectares must be greater than zero")
        if cause:
            return Refusal(cause, "you own %.6g hectares of farmland, not %.6g" % (owned, hectares), owned=owned, hectares=hectares)
        price = hectares * self.farm_land_price()
        holdings.farm_hectares = owned - hectares
        self.needs.send(ReceiveFromEdge(edges.EDGE_LANDOWNERS, price, "farmland sold"))
        return {"hectares": hectares, "price": price, "remaining": holdings.farm_hectares}
