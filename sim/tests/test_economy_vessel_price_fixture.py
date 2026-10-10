"""A cheap durable made from a dug input (a vessel from clay) does not stay dear over decades in a small economy
(Complaint 434, the vessels item). The figures are the fixture's own; nothing is read from data/."""
import dataclasses
import unittest

from sim.economy import unit_cost
from sim.economy.economy import Economy
from sim.economy.households_basket import Basket, NeedSpec
from sim.economy.types import GoodSpec, Recipe
from sim.tests import economy_fixture as fixture
from sim.world.need_demand import NEED_SUBSTITUTION_ELASTICITY

QUICK_TOPIC = True

VESSEL, CLAY = "ceramic_kg", "clay_kg"
FIRE = Recipe("fire_ceramic", {VESSEL: 1000.0}, {CLAY: 1600.0}, {fixture.SMITH: 60.0})
DIG = Recipe("dig_clay", {CLAY: 1000.0}, {}, {fixture.MINER: 80.0})
OPENING_PRICE = 0.2
YEARS = 40
LATE_YEARS = 10
LATE_PRICE_OVER_OPENING = 3.0
SETTLING_YEARS = 6                 # the opening prices are guesses; the first years find the market's own level
INPUT_YEAR_TO_YEAR_RATIO = 2.5     # a thin dug input's price moves by less than this factor between years


def vessel_setup():
    base = fixture.small_setup()
    specs = dict(base.specs)
    specs[VESSEL] = GoodSpec(VESSEL, 1.0, 0.0, 4.0, "vessels")
    specs[CLAY] = GoodSpec(CLAY, 1.0, 0.0, 0.0, "clay")
    needs = base.basket.needs + (NeedSpec("vessels", 1.25, 0.02, ((VESSEL, 1.0),)),)
    need_data = dict(base.basket.need_data)
    need_data["vessels"] = {"surplus_budget_share": 0.02}
    recipes = dict(base.recipes)
    recipes.update({FIRE.recipe_id: FIRE, DIG.recipe_id: DIG})
    prices = dict(base.opening_prices)
    prices.update({VESSEL: OPENING_PRICE, CLAY: 0.01})
    return dataclasses.replace(base, specs=specs, recipes=recipes, opening_prices=prices,
                               basket=Basket(needs, NEED_SUBSTITUTION_ELASTICITY, need_data))


def price_path(good=VESSEL):
    setup = vessel_setup()
    economy = Economy(setup)
    rows = []
    for _year in range(YEARS):
        outcome = economy.step(fixture.quiet_year(setup))
        cost = unit_cost.variable_cost_per_run(FIRE, outcome.prices, outcome.wages) / FIRE.outputs[VESSEL]
        rows.append((outcome.prices.get(good, 0.0), cost))
    return rows


class VesselPriceTests(unittest.TestCase):
    def test_the_vessel_price_after_decades_stays_within_a_small_multiple_of_the_opening_price(self):
        late = [price for price, _cost in price_path()[-LATE_YEARS:]]
        self.assertLess(sum(late) / len(late), LATE_PRICE_OVER_OPENING * OPENING_PRICE)

    def test_the_dug_input_price_does_not_swing_between_years_once_the_market_has_settled(self):
        prices = [price for price, _cost in price_path(CLAY)][SETTLING_YEARS:]
        worst = max(max(after / before, before / after) for before, after in zip(prices, prices[1:]))
        self.assertLess(worst, INPUT_YEAR_TO_YEAR_RATIO)

    def test_the_vessel_sells_at_a_price_above_what_its_inputs_cost(self):
        rows = price_path()[-LATE_YEARS:]
        self.assertGreater(sum(price for price, _cost in rows), sum(cost for _price, cost in rows))


if __name__ == "__main__":
    unittest.main()
