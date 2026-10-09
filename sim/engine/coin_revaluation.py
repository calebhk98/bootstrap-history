"""A coin is a fixed weight of its metal, so it is worth what that metal is worth on the market.

Each year's close records the market's price ratio of every coin metal (the home society's and each
partner's). A glut of the metal (ratio below one) makes a unit of coin buy less of everything, so the
price level rises with it; a shortage lowers it. Holders of coin and of debts written in coin bear the
change: nothing is indexed or compensated.
"""
from sim.constants import declare

from .data import load_civ

REVALUATION_YEARLY_SHARE = declare(
    "REVALUATION_YEARLY_SHARE", 0.5, kind="temporary_heuristic",
    unit="share of the gap between the coin metal's recorded and measured value closed in a year",
    source=None, confidence="D",
    why="Coin is a stock: its value follows the metal's price as holders and mints reprice, not at once. "
        "Damping also keeps one year's market noise out of the price level. Mint behaviour would replace it.")


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
            measured = self.real_price_ratio(metal)
            if not measured > 0.0:
                measured = 1.0
            held = ratios.get(metal, 1.0)
            ratios[metal] = held ** (1.0 - REVALUATION_YEARLY_SHARE) * measured ** REVALUATION_YEARLY_SHARE
