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


TRINKET, CARVE = "trinket", "carve_trinket"


def variety_setup():
    """The fixture with a trinket, bought only for ornament (a variety good, no floor)."""
    recipes = fixture.recipes()
    recipes[CARVE] = Recipe(CARVE, {TRINKET: 10.0}, {}, {fixture.SMITH: 10.0})
    specs = fixture.specs()
    specs[TRINKET] = dataclasses.replace(specs[fixture.METAL], good_id=TRINKET, category="ornament")
    basket = fixture.basket()
    needs = tuple(dataclasses.replace(need, goods=need.goods + ((TRINKET, 1.0),)) if need.need_id == fixture.ORNAMENT
                  else need for need in basket.needs)
    prices = dict(fixture.small_setup().opening_prices, **{TRINKET: 1.5})
    return fixture.small_setup(recipes=recipes, specs=specs, basket=dataclasses.replace(basket, needs=needs),
                               opening_prices=prices)


class StuckMarketTests(unittest.TestCase):
    def _capacity(self, economy, recipe_id):
        return sum(producer.capacity_runs for producer in economy.record.producers.values()
                   if producer.recipe_id == recipe_id)

    def _shrunk(self, setup, recipe_id, share):
        economy = Economy(setup)
        for producer_id, producer in list(economy.record.producers.items()):
            if producer.recipe_id == recipe_id:
                economy.record.producers[producer_id] = dataclasses.replace(
                    producer, capacity_runs=producer.capacity_runs * share)
        return economy

    def test_a_variety_good_left_with_few_makers_is_competed_back_toward_cost(self):
        setup = variety_setup()
        economy = self._shrunk(setup, CARVE, 0.05)
        start = self._capacity(economy, CARVE)
        prices = [economy.step(fixture.quiet_year(setup)).prices.get(TRINKET) for _year in range(20)]
        self.assertGreater(self._capacity(economy, CARVE), 2.0 * start)
        self.assertLess(prices[-1], 0.5 * max(prices[:5]))
        self.assertEqual(economy.record.book.check_conservation(1e-6).breaches, ())

    def test_a_staple_bought_to_a_floor_draws_no_margin_entrant(self):
        self.assertFalse(entry_margin.demand_is_elastic(100.0, 2.0, 105.0, 1.0))
        self.assertTrue(entry_margin.demand_is_elastic(100.0, 2.0, 300.0, 1.0))

    def test_no_newcomer_where_no_buyer_bid(self):
        setup = fixture.small_setup()
        economy = Economy(setup)
        economy.step(fixture.quiet_year(setup))
        view = economy.view()
        bids = {(fixture.GRAIN, area.area_id): [] for area in economy.area_map.areas(fixture.GRAIN)}
        self.assertEqual(entry_margin.margin_entry_plans(setup, economy.record, view, economy.area_map, bids), [])


if __name__ == "__main__":
    unittest.main()
