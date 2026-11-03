"""Who offers a good, and what households are asked to pay for it.

A good is offered by a modelled seller or it cannot be had, and a good no one offers has no price. The
seller is the home society (a technique it holds, or one within reach of what it holds, in the price
table); the partner countries sell through the agent economy's own markets. A good no one offers is
unavailable: it has no price, cannot be bought, and anything that needs it cannot start until a seller
appears.
"""
from .goods_imports import HOME_SELLER


class GoodsOffers:
    """Reads of who sells what (`goods_market.offers`)."""

    def __init__(self, sim):
        self._sim = sim

    def home_prices(self):
        """{material: money per unit} the home society's sellers ask at the acting tile: the economy's price, for the
        goods it has a market for; a good it has none for is absent, not priced at its cost. While the economy opens the
        cost table answers (the opening is built from it). The same object while neither has changed."""
        sim = self._sim
        table = sim._material_prices()
        paid = sim.economy.agent_prices_at()
        if paid is None:
            return table
        held = sim.remembered("home_prices")
        if held is not None and held[0] is table and held[1] is paid:
            return held[2]
        merged = {material: paid[material] for material in table if material in paid}
        sim.remember("home_prices", (table, paid, merged))
        return merged

    def home_unit_price(self, material):
        """Money per unit the home society's sellers ask for a material (or a curated commodity, by the material
        it is priced as) at the acting tile; None when no home seller offers it. The one price of the coin metal
        in the mint and in cargo."""
        prices = self.home_prices()
        key = self._sim._priced_key(material, prices)
        return None if key is None else prices[key]

    def _worked_out_offers(self):
        """(household prices, seller of each material): every priced material has the home society as its seller. The
        same objects while the home prices are the same object."""
        sim = self._sim
        prices = self.home_prices()
        cache = sim.remembered("goods_offers")
        if cache is not None and cache[0] is prices:
            return cache[1], cache[2]
        sellers = {material: HOME_SELLER for material in prices}
        sim.remember("goods_offers", (prices, prices, sellers))
        return prices, sellers

    def household_prices(self):
        """{material: money per unit} households are asked to pay: the economy's price on the acting tile where the
        home society makes it and the economy has a market for it (the cost of making while the economy opens),
        nothing where no one does. The same object while the home prices have not changed."""
        return self._worked_out_offers()[0]

    def unit_price(self, material):
        """Money per unit to buy a material (the home sellers' price on the acting tile), or None when no one in
        reach sells it."""
        price = self.home_unit_price(material)
        return price if price is not None else self.household_prices().get(material)

    def can_be_bought(self, material):
        return self.unit_price(material) is not None

    def offered_by(self, material):
        """HOME_SELLER when a technique the society holds or can reach makes the material, None when nothing does."""
        return self._worked_out_offers()[1].get(material)
