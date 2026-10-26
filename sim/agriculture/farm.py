"""The farmland the acting seat holds: what it is worth, buying it and selling it back.

The holding itself (hectares, granary stock, last harvest) is the demography module's seat state, read through its view
`farm_holdings` and changed by its command `ChangeFarmland`."""
from sim.agents.api import edges
from sim.demography.api import ChangeFarmland
from sim.ledger.api import PayEdge, ReceiveFromEdge
from sim.refusal import Refusal

from . import rules
from .constants import FARM_LABOUR_HOURS_PER_HA


class Farm:

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
        self.needs.send(ChangeFarmland(hectares))
        return hectares

    def sell_farm(self, command):
        hectares = float(command.hectares)
        owned = self.needs.farm_holdings()["hectares"] or 0.0
        cause = rules.sale_refusal(hectares, owned)
        if cause == "not_positive":
            return Refusal(cause, "hectares must be greater than zero")
        if cause:
            return Refusal(cause, "you own %.6g hectares of farmland, not %.6g" % (owned, hectares), owned=owned, hectares=hectares)
        price = hectares * self.farm_land_price()
        remaining = self.needs.send(ChangeFarmland(-hectares))
        self.needs.send(ReceiveFromEdge(edges.EDGE_LANDOWNERS, price, "farmland sold"))
        return {"hectares": hectares, "price": price, "remaining": remaining}
