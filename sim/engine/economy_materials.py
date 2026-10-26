"""What the markets topic still reads through `Sim` from the old raw-material supply: the founder's trade at the goods market.

The supply, demand, throttle, electricity and project bills are the materials module's (sim/materials/); the commodity
catalogue, the price lookups and the memos are the prices module's (sim/prices/). What remains here goes with the markets
module."""


class MaterialSupplyMixin:

    def material_trade_quote(self, material):
        """Current buy/sell quote for one tonne of a material commodity."""
        return self.goods_market.quote(material)

    def buy_material_stock(self, material, tonnes):
        """The founder buys a material at the market (see GoodsMarket.buy)."""
        return self.goods_market.buy(self.goods_market.acting, material, tonnes)

    def sell_material_stock(self, material, tonnes):
        """The founder sells stock at the market (see GoodsMarket.sell)."""
        return self.goods_market.sell(self.goods_market.acting, material, tonnes)

    def material_purchase_cost(self, material, tonnes, already=0.0):
        """(money, mean money per tonne) to buy `tonnes` of a material now, the price rising as the order is filled. None
        when it has no price (see GoodsMarket.quote_buy)."""
        return self.goods_market.quote_buy(material, tonnes, already)
