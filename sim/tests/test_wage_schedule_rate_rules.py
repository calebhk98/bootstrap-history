"""build_schedule prices training at the civilisation's own interest rate; the opening recipes price ink, a written
page and a tallow candle."""

QUICK_TOPIC = True

import unittest

from sim.economy.recipes import recipes_from_production_data
from sim.engine import data, wage_schedule
from sim.labour import wages
from sim.world import demand

GOODS = ("ink_kg", "written_page", "light_tallow_candle")


class TrainingPremium(unittest.TestCase):

    def test_the_schedule_prices_training_at_the_civilisations_rate(self):
        civ = data.load_civ("rome_100ad")
        schedule = wage_schedule.build_schedule(data.TRADE_REGISTRY, civ)
        years = schedule.training_years["smith"]
        self.assertAlmostEqual(schedule.premium("smith"), wages.training_premium(years, civ["starting_interest_rate"]))

    def test_a_dearer_rate_gives_a_larger_premium(self):
        civ = dict(data.load_civ("rome_100ad"))
        low = wage_schedule.build_schedule(data.TRADE_REGISTRY, dict(civ, starting_interest_rate=0.02)).premium("smith")
        high = wage_schedule.build_schedule(data.TRADE_REGISTRY, dict(civ, starting_interest_rate=0.20)).premium("smith")
        self.assertGreater(high, low)


class WrittenGoodsHaveRecipes(unittest.TestCase):

    def test_ink_a_page_and_a_tallow_candle_are_each_made_by_some_recipe(self):
        recipes = recipes_from_production_data(demand.production_data())
        made = {good for recipe in recipes.values() for good in recipe.outputs}
        self.assertEqual([good for good in GOODS if good not in made], [])


if __name__ == "__main__":
    unittest.main()
