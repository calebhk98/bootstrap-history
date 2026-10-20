"""Complaint 473: the opening's basket (what households are seeded to want, and the weights of the price level index)
agrees with the supply the opening builds, good by good, so no good enters the index with a quantity it cannot make."""
import dataclasses
import unittest

from sim.economy import api as economy_api
from sim.economy import opening
from sim.economy.types import Recipe, SiteLimit
from sim.tests import economy_fixture as fixture
from sim.tests import harness

BAND = 1.05      # the basket may exceed what is left for households by rounding only


def left_for_households(setup, record):
    """What the opening's producers expect to sell of each good, less what their own expected runs use up of it."""
    made, used = {}, {}
    for producer in record.producers.values():
        recipe = setup.recipes[producer.recipe_id]
        for good, quantity in recipe.outputs.items():
            made[good] = made.get(good, 0.0) + producer.expected_sales * producer.yield_factor * quantity
        for good, quantity in recipe.inputs.items():
            used[good] = used.get(good, 0.0) + producer.expected_sales * quantity
        if recipe.plant_life_years > 0.0:
            for good, quantity in recipe.plant_goods.items():
                used[good] = used.get(good, 0.0) + producer.expected_sales * quantity / recipe.plant_life_years
    return {good: made.get(good, 0.0) - used.get(good, 0.0) for good in set(made) | set(used)}


def goods_over_supply(setup, record):
    left = left_for_households(setup, record)
    return {good: wanted / left.get(good, 0.0) if left.get(good, 0.0) > 0.0 else float("inf")
            for good, wanted in record.opening_basket.items() if wanted > BAND * max(left.get(good, 0.0), 0.0)}


def limited_metal_setup(mine_runs):
    recipes = fixture.recipes()
    recipes[fixture.MINE] = dataclasses.replace(recipes[fixture.MINE], site_bound=True)
    return fixture.small_setup(recipes=recipes, site_limits=(SiteLimit(fixture.MINE, fixture.HILLS, mine_runs, 1.0),))


class OpeningBasketAgreesTests(unittest.TestCase):
    def test_a_good_a_deposit_cannot_supply_enters_the_basket_at_the_quantity_supplied(self):
        setup = limited_metal_setup(mine_runs=0.5)
        record, _areas, _carriage = opening.open_economy(setup)
        self.assertEqual(goods_over_supply(setup, record), {})

    def test_where_supply_is_ample_the_basket_is_the_final_demand(self):
        setup = limited_metal_setup(mine_runs=1.0e6)
        record, _areas, _carriage = opening.open_economy(setup)
        self.assertEqual(goods_over_supply(setup, record), {})
        self.assertGreater(sum(record.opening_basket.values()), 0.0)

    def test_the_fixture_economy_basket_agrees_with_its_supply(self):
        setup = fixture.small_setup()
        record, _areas, _carriage = opening.open_economy(setup)
        self.assertEqual(goods_over_supply(setup, record), {})


class RomeOpeningBasketTests(unittest.TestCase):
    def test_no_good_in_the_rome_basket_exceeds_its_supply_and_the_index_starts_at_one(self):
        from sim.engine.economy_port_setup import build_setup
        game = harness.sim()
        setup = build_setup(game, game.state.economy.agent_economy["opening"])
        economy = economy_api.blank_economy(setup)
        self.assertEqual(goods_over_supply(setup, economy.record), {})
        weights = economy.record.opening_basket
        from sim.economy import currency
        self.assertEqual(currency.basket_price_level(setup.opening_prices, setup.opening_prices, weights), 1.0)


if __name__ == "__main__":
    unittest.main()
