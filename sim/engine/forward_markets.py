"""One-line forwarders from the old `Sim` names of the markets topic to the markets module, for callers not yet in a module.

The goods market and the port over the agent economy are the markets module's (`economy`, `goods_market`); the screens, the port and the goods
market itself still say `sim._market_flows()`, `sim.market_state(...)` or `sim.buy_material_stock(...)`. Each line goes when its
last caller reads the view (`sim.view(name)`) or sends the command (`sim.send(command)`) itself."""
from sim.markets import categories
from sim.markets.api import BuyMaterial, OpenMarketBook, SellMaterial


class ForwardMarketsMixin:

    # numbers the actors module reads off the game through `legacy_constant`
    GOODS_CATEGORIES = categories.GOODS_CATEGORIES
    ESSENTIAL_CATEGORIES = categories.ESSENTIAL_CATEGORIES

    @property
    def goods_market(self):
        """The one goods market every buyer and seller asks (the markets module's)."""
        return self.assembly.modules["markets"].goods_market

    @property
    def economy(self):
        """The port over the agent economy (the markets module's)."""
        return self.assembly.modules["markets"].economy

    # ---- the book and the year's flows ----

    def _market_flows(self):
        return self.view("legacy_market_flows")()

    def _market_entry(self, commodity):
        return self.view("market_entry")[commodity]

    def market_state(self, material):
        return self.view("market_state")[material]

    def _open_market_book(self):
        return self.send(OpenMarketBook())

    def _opening_population(self):
        return self.view("opening_population")()

    # ---- the goods categories and what the screens read ----

    def _goods_category_ratios(self, category, extra=0):
        return self.view("goods_category_ratios")(category, extra)

    def essential_price_ratio(self):
        return self.view("essential_price_ratio")()

    def market_absorption_by_category(self, deduction):
        return self.view("market_absorption_by_category")(deduction)

    # ---- the founder at the market ----

    def material_trade_quote(self, material):
        return self.view("goods_quote")[material]

    def material_purchase_cost(self, material, tonnes, already=0.0):
        return self.view("purchase_quote")(material, tonnes, already)

    def buy_material_stock(self, material, tonnes):
        return self.send(BuyMaterial(material, tonnes))

    def sell_material_stock(self, material, tonnes):
        return self.send(SellMaterial(material, tonnes))
