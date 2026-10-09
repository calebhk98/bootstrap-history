"""A coin is a fixed weight of its metal, so it is worth what that metal is worth on the market.

Each year's close records the market's price ratio of every coin metal (the home society's and each
partner's). A glut of the metal (ratio below one) makes a unit of coin buy less of everything, so the
price level rises with it; a shortage lowers it. Holders of coin and of debts written in coin bear the
change: nothing is indexed or compensated.
"""
from .data import load_civ


class CoinRevaluationMixin:

    def coin_metal_ratio(self, material):
        """The market's price over the incumbents' cost for a coin metal, as of the last year's close."""
        return self.state.economy.coin_metal_ratios.get(material, 1.0)

    def home_coin_metal(self):
        return self.civ["coin_standard"]["material"]

    def partner_coin_metal(self, civilization_id):
        return load_civ(civilization_id)["coin_standard"]["material"]

    def revalue_coin_metals(self):
        """Record the market ratio of the home coin metal and of each partner's."""
        metals = {self.home_coin_metal()}
        metals.update(self.partner_coin_metal(partner) for partner in self.foreign_economies())
        ratios = self.state.economy.coin_metal_ratios
        for metal in sorted(metals):
            ratio = self.market_price_ratio(metal)
            ratios[metal] = ratio if ratio and ratio > 0.0 else 1.0
