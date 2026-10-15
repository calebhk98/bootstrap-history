"""A partner's coin is worth what it buys at home, which follows the goods, not the wage: its metal is counted at the
price the economy shows for that metal on the acting tile, the one number the mint, the cargo and the partners'
payments all use (Complaint 507, stage 3)."""

QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.engine import purchase_rule  # noqa: F401  (first: the engine modules import each other in a fixed order)
from sim.engine.trader_cargo import TraderCargoMixin
from sim.tests.test_goods_market_pays_economy_price import TILE_PRICE_PER_UNIT, stub_game


class Cargo(TraderCargoMixin):
    def __init__(self):
        _game, self.goods_market = stub_game()


def partner_with(material, kg_per_unit):
    return mock.patch("sim.engine.trader_cargo.load_civ",
                      lambda partner: {"coin_standard": {"material": material, "kg_per_unit": kg_per_unit}})


class PartnerCoinTests(unittest.TestCase):

    def test_a_partners_coin_is_worth_its_metal_at_the_economys_price(self):
        with partner_with("silver_kg", 0.0027):
            self.assertAlmostEqual(Cargo()._money_per_partner_coin("partner"), 0.0027 * TILE_PRICE_PER_UNIT["silver_kg"])

    def test_a_coin_metal_the_economy_does_not_price_leaves_the_coin_unpriced(self):
        with partner_with("platinum_kg", 0.01):
            self.assertIsNone(Cargo()._money_per_partner_coin("partner"))

    def test_the_coin_is_worth_more_when_the_economys_price_of_its_metal_is_higher(self):
        cargo = Cargo()
        with partner_with("silver_kg", 0.0027):
            before = cargo._money_per_partner_coin("partner")
            TILE_PRICE_PER_UNIT["silver_kg"] *= 2.5
            try:
                self.assertAlmostEqual(cargo._money_per_partner_coin("partner"), before * 2.5)
            finally:
                TILE_PRICE_PER_UNIT["silver_kg"] /= 2.5


if __name__ == "__main__":
    unittest.main()
