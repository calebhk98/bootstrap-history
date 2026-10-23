"""Complaints 345 and 341: a concern's running costs and takings are its own (no index of the economy's output scales
either), the founder and an actor are quoted the same upkeep for the same concern, and a goods category's takings are the
market's price times volume shared among its sellers. Rules: `node_upkeep.non_labour_upkeep_money`,
`EconomyPort.concern_upkeep` against `ProductionMixin.institution_upkeep` (the founder's), and
`goods_seller_share.seller_revenue_factor`. That pay follows output per head by a share is test_concern_volume; the one
wage for every employer is test_one_labour_market_wiring."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.engine import node_upkeep
from sim.engine.economy_port import EconomyPort
from sim.engine.economy_production import ProductionMixin
from sim.engine.goods_seller_share import seller_revenue_factor
from sim.engine.projects_venture_quotes import VentureQuotesMixin

NODE = {"up": 5000.0, "_upkeep_hours_parts": None, "_upkeep_basis": None}


class Founder(ProductionMixin, VentureQuotesMixin):
    """The founder's side of a plain concern: no scalable institution, no capability gate."""

    SCALABLE_INSTITUTIONS = ()
    CAPABILITY_INSTITUTIONS = ()

    def __init__(self, price_index):
        self.nodes = {"shop": NODE}
        self.price_index = price_index

    def mechanic(self, node_id, name):
        return None


class UpkeepTests(unittest.TestCase):
    def test_upkeep_is_the_stated_figure_times_the_non_crew_share_the_scale_and_the_capacity(self):
        share = node_upkeep.non_labour_share(NODE)
        self.assertAlmostEqual(node_upkeep.non_labour_upkeep_money(5000.0, NODE, 2.0, 1.5), 5000.0 * share * 1.5 * 2.0)

    def test_the_founder_and_an_actor_pay_the_same_upkeep_for_the_same_concern(self):
        price_index = 1.7
        founder = Founder(price_index)
        port = EconomyPort(SimpleNamespace(nodes={"shop": NODE}, price_index=price_index))
        self.assertAlmostEqual(founder.venture_real_upkeep("shop"), port.concern_upkeep("shop"), places=9)

    def test_a_dearer_price_level_raises_both_alike(self):
        self.assertAlmostEqual(Founder(2.0).venture_real_upkeep("shop"), 2.0 * Founder(1.0).venture_real_upkeep("shop"))
        low = EconomyPort(SimpleNamespace(nodes={"shop": NODE}, price_index=1.0)).concern_upkeep("shop")
        high = EconomyPort(SimpleNamespace(nodes={"shop": NODE}, price_index=2.0)).concern_upkeep("shop")
        self.assertAlmostEqual(high, 2.0 * low)


class CategoryShareTests(unittest.TestCase):
    def test_every_seller_gets_one_share_of_the_markets_price_times_volume(self):
        market_total = 1.3 * 0.9
        for sellers in (1, 4, 9):
            share = seller_revenue_factor(1.3, 0.9, sellers)
            self.assertAlmostEqual(share * sellers, market_total)

    def test_more_sellers_in_a_category_each_take_less(self):
        self.assertLess(seller_revenue_factor(1.0, 1.0, 5), seller_revenue_factor(1.0, 1.0, 4))

    def test_a_dearer_price_or_a_bigger_volume_raises_each_sellers_share(self):
        base = seller_revenue_factor(1.0, 1.0, 4)
        self.assertGreater(seller_revenue_factor(1.2, 1.0, 4), base)
        self.assertGreater(seller_revenue_factor(1.0, 1.2, 4), base)

    def test_a_good_that_is_not_an_essential_is_lifted_or_dampened_by_the_income_effect(self):
        self.assertAlmostEqual(seller_revenue_factor(1.0, 1.0, 2, 1.4), 0.7)
        self.assertAlmostEqual(seller_revenue_factor(1.0, 1.0, 2, 0.8), 0.4)

    def test_an_essential_category_takes_no_income_effect(self):
        self.assertAlmostEqual(seller_revenue_factor(1.0, 1.0, 2), 0.5)


if __name__ == "__main__":
    unittest.main()
