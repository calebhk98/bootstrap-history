"""Complaints 345 and 341: a concern's running costs and takings are its own (no index of the economy's output scales
either), the founder and an actor are quoted the same upkeep for the same concern, and a goods category's takings are the
market's price times volume shared among its sellers. Rules: `node_upkeep.non_labour_upkeep_money`,
`EconomyPort.concern_upkeep` against the production module's `institution_upkeep` (the founder's), and
`rules.seller_revenue_factor`. That pay follows output per head by a share is test_concern_volume; the one
wage for every employer is test_one_labour_market_wiring."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.production import node_upkeep
from sim.markets.port import EconomyPort
from sim.markets.rules import seller_revenue_factor
from sim.engine.projects_venture_quotes import VentureQuotesMixin
from sim.tests import production_host

NODE = {"up": 5000.0, "_upkeep_hours_parts": {"staff": 3.0, "plant": 1.0}, "_upkeep_basis": None}   # a quarter of the upkeep is not crew


class Founder(VentureQuotesMixin):
    """The founder's side of a plain concern: no scalable institution, no capability gate."""

    def __init__(self, price_index):
        self.nodes = {"shop": NODE}
        self.price_index = price_index
        self.production = production_host.build(self, capability_sets=((), (), {}))

    def institution_upkeep(self, node_id, units=None, fully_staffed=False):
        return self.production.institution_upkeep(node_id, units, fully_staffed)


class UpkeepTests(unittest.TestCase):
    def test_upkeep_is_the_stated_figure_times_the_non_crew_share_the_scale_and_the_capacity(self):
        self.assertAlmostEqual(node_upkeep.non_labour_upkeep_money(5000.0, NODE, 2.0, 1.5), 5000.0 * 0.25 * 1.5 * 2.0)

    def test_an_actors_concern_upkeep_is_the_non_crew_part_at_the_price_level(self):
        port = EconomyPort(SimpleNamespace(nodes={"shop": NODE}, price_index=1.7))
        self.assertAlmostEqual(port.concern_upkeep("shop"), 5000.0 * 0.25 * 1.7)

    def test_the_founders_quote_of_the_same_concern_is_the_non_crew_part_at_the_price_level(self):
        self.assertAlmostEqual(Founder(1.7).venture_real_upkeep("shop"), 5000.0 * 0.25 * 1.7)


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
