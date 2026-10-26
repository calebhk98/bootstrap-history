"""A partner's coin is worth what it buys at home, which follows the goods, not the wage: its metal is counted at the
price the economy shows for that metal on the acting tile, the one number the mint, the cargo and the partners'
payments all use (Complaint 507, stage 3)."""

QUICK_TOPIC = True

import unittest

from sim.engine import purchase_rule  # noqa: F401  (first: the engine modules import each other in a fixed order)
from sim.foreign_trade.module import ForeignTrade
from sim.tests import module_harness
from sim.tests.test_goods_market_pays_economy_price import TILE_PRICE_PER_UNIT, stub_game


def cargo_of_partner_with(material, kg_per_unit):
    """The foreign-trade module over a partner whose coin is `kg_per_unit` of `material`, the metal priced as the economy's
    tile prices it."""
    _game, goods_market = stub_game()
    return module_harness.build(ForeignTrade, views={
        "civilisation_record": lambda partner: {"coin_standard": {"material": material, "kg_per_unit": kg_per_unit}},
        "home_unit_price": goods_market.home_unit_price})


class PartnerCoinTests(unittest.TestCase):

    def test_a_partners_coin_is_worth_its_metal_at_the_economys_price(self):
        cargo = cargo_of_partner_with("silver_kg", 0.0027)
        self.assertAlmostEqual(cargo.money_per_partner_coin("partner"), 0.0027 * TILE_PRICE_PER_UNIT["silver_kg"])

    def test_a_coin_metal_the_economy_does_not_price_leaves_the_coin_unpriced(self):
        self.assertIsNone(cargo_of_partner_with("platinum_kg", 0.01).money_per_partner_coin("partner"))

    def test_the_coin_is_worth_more_when_the_economys_price_of_its_metal_is_higher(self):
        cargo = cargo_of_partner_with("silver_kg", 0.0027)
        before = cargo.money_per_partner_coin("partner")
        TILE_PRICE_PER_UNIT["silver_kg"] *= 2.5
        try:
            self.assertAlmostEqual(cargo.money_per_partner_coin("partner"), before * 2.5)
        finally:
            TILE_PRICE_PER_UNIT["silver_kg"] /= 2.5


if __name__ == "__main__":
    unittest.main()
