"""Newcomers drawn by a margin: a market selling far above cost gains makers until its price nears cost."""
import dataclasses
import math
import unittest

from sim.economy import entry_margin
from sim.economy.economy import Economy
from sim.economy.types import Recipe
from sim.tests import economy_fixture as fixture

SMELT = Recipe("smelt", {"metal": 10.0, "slag": 90.0}, {"ore": 100.0}, {"smith": 5.0},
               plant_goods={"stone": 2.0}, plant_life_years=10.0)


class FullCostTests(unittest.TestCase):
    def test_cost_shares_a_joint_run_by_value_and_counts_the_plant(self):
        prices = {"metal": 9.0, "slag": 0.1}
        cost = entry_margin.full_cost_per_unit(SMELT, "metal", prices, {"ore": 0.5, "stone": 1.0}, {"smith": 2.0}, 0.0)
        run_cost = 100.0 * 0.5 + 5.0 * 2.0 + 2.0 * 1.0 / 10.0
        share = 90.0 / (90.0 + 9.0)
        self.assertAlmostEqual(cost, run_cost * share / 10.0)

    def test_an_input_with_no_price_cannot_be_costed(self):
        self.assertTrue(math.isinf(entry_margin.full_cost_per_unit(SMELT, "metal", {"metal": 9.0}, {}, {"smith": 2.0}, 0.0)))


class StuckMarketTests(unittest.TestCase):
    def _shrunk(self, share):
        setup = fixture.small_setup()
        economy = Economy(setup)
        for producer_id, producer in list(economy.record.producers.items()):
            if producer.recipe_id == fixture.FARM:
                economy.record.producers[producer_id] = dataclasses.replace(
                    producer, capacity_runs=producer.capacity_runs * share)
        return setup, economy

    def _capacity(self, economy):
        return sum(producer.capacity_runs for producer in economy.record.producers.values()
                   if producer.recipe_id == fixture.FARM)

    def test_a_market_left_with_few_makers_is_competed_back_toward_cost(self):
        setup, economy = self._shrunk(0.05)
        start = self._capacity(economy)
        prices = [economy.step(fixture.quiet_year(setup)).prices[fixture.GRAIN] for _year in range(15)]
        self.assertGreater(self._capacity(economy), 4.0 * start)
        self.assertLess(prices[-1], 0.5 * max(prices[:3]))
        self.assertEqual(economy.record.book.check_conservation(1e-6).breaches, ())

    def test_no_newcomer_where_no_buyer_bid(self):
        setup = fixture.small_setup()
        economy = Economy(setup)
        economy.step(fixture.quiet_year(setup))
        view = economy.view()
        bids = {(fixture.GRAIN, area.area_id): [] for area in economy.area_map.areas(fixture.GRAIN)}
        self.assertEqual(entry_margin.margin_entry_plans(setup, economy.record, view, economy.area_map, bids), [])


if __name__ == "__main__":
    unittest.main()
