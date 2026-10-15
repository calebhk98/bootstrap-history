"""What an actor pays to buy a material and is paid to sell it: the economy's price on its tile, carriage, and the
climb of that price over the order.

The price is the one the agent economy shows on the acting tile (`EconomyPort.agent_prices_at`); a good it has no
market for costs what a held technique makes it for (the cost table), and a good only a partner makes costs the
partner's landed price. Carriage is the haul from where the material comes from, on top of the price where it is
sold. The climb is the economy's own price response (`api.price_response`): its last book cleared again with the
order as one more bid, or the sale as one more offer. A buyer's own earlier purchases this year count as part of
the order, since the economy has not yet seen them. Nothing here reads a ratio of the market to the cost table.
"""
import math

from .goods_market_imports import HOME_SELLER
from .material_units import tonnes_per_unit

# Points along an order at which the economy's response is read; the order's mean climb is their mean.
PRICE_SLICES = 8


class GoodsPricing:
    """Mixin of `GoodsOffers`: the price at the acting tile, carriage and the climb over an order."""

    def making_cost_per_tonne(self, material):
        """Money per tonne it costs the home society to make a material (the cost table); None when no technique
        in reach makes it."""
        cost = self._sim._material_price_per_kg(material)
        return None if cost is None else cost / tonnes_per_unit(material)

    def price_at_tile_per_tonne(self, material):
        """Money per tonne to buy a material from the cheapest seller in reach before carriage: the economy's price
        on the acting tile, else what a technique makes it for, else a partner's landed price; None when no one in
        reach sells it."""
        per_unit = self.unit_price(material)
        return None if per_unit is None else per_unit / tonnes_per_unit(material)

    def _carriage_per_tonne(self, material, price_per_tonne):
        """Money per tonne to carry a material the home sells to the buyer; a partner's landed price already holds
        its freight."""
        if self.offered_by(material) not in (None, HOME_SELLER):
            return 0.0
        return self._sim.material_carriage_per_tonne(self._sim._material_tag(material)[0], price_per_tonne)

    def _economy_good(self, material):
        """The key the economy trades a material under (a curated commodity is traded as the material it is priced as),
        or None when a partner is its only seller."""
        if self.offered_by(material) not in (None, HOME_SELLER):
            return None
        return self._sim._priced_key(material, self._home_prices())

    def _climb(self, material, taken_before, tonnes, selling=False):
        """Mean factor on the price while buying (or selling) `tonnes` more of a material after `taken_before`
        tonnes bought (or sold) this year or in the same bill, read from the economy's book at points along the
        order. One where the economy has no book for the good."""
        good = self._economy_good(material)
        economy = self._sim.economy
        if good is None or taken_before + tonnes <= 0.0:
            return 1.0
        tile = economy.acting_tile()
        offered = economy.agent_offered_tonnes(good, tile)
        slices = PRICE_SLICES if tonnes > 0.0 else 1
        total = 0.0
        for index in range(slices):
            along = taken_before + (tonnes * (index + 0.5) / slices if tonnes > 0.0 else 0.0)
            if not selling and offered is not None:
                along = min(along, offered * (1.0 - 0.5 / slices))    # the last tonne the sellers hold is the dearest
            if along <= 0.0:
                total += 1.0
                continue
            factor = economy.agent_price_response(good, along if selling else 0.0, 0.0 if selling else along, tile)
            total += 1.0 if factor is None or not math.isfinite(factor) else factor
        return total / slices

    def _bought_this_year(self, material):
        """Tonnes the asking seat has taken from the market this year in the material's commodity, bought or
        drawn by its running works."""
        commodity = self._sim._material_tag(material)[0]
        return self.bought_tonnes(commodity, self.acting_party_id) + self.drawn_tonnes(commodity)

    def purchase_cost(self, material, tonnes, already=0.0):
        """(money, mean money per tonne) to buy `tonnes` of a material now: the price on the acting tile climbing
        with the order, after `already` tonnes of it in the same bill and what the seat bought this year, and
        carriage on top. None when it has no price."""
        price = self.price_at_tile_per_tonne(material)
        if price is None:
            return None
        tonnes = max(0.0, tonnes)
        mean = (price * self._climb(material, already + self._bought_this_year(material), tonnes)
                + self._carriage_per_tonne(material, price))
        return mean * tonnes, mean

    def quote_buy(self, material, tonnes, already=0.0):
        """What an order of `tonnes` costs: (money, mean money per tonne), or None."""
        return self.purchase_cost(material, tonnes, already)

    def sale_proceeds(self, material, tonnes, already=0.0):
        """(money, mean money per tonne) for selling `tonnes` more after `already` tonnes sold this year: the
        price on the acting tile falling as the sale adds to what is offered there (the economy's response). The
        seller is not charged carriage, so there is no fixed spread between buying and selling."""
        price = self.price_at_tile_per_tonne(material)
        if price is None or tonnes < 0.0:
            return 0.0, 0.0
        mean = price * self._climb(material, already, tonnes, selling=True)
        return mean * tonnes, mean
