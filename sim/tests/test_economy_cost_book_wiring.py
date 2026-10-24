"""Complaints/507 stage 5, wiring on stand-ins: `economy_cost_book` hands the cost calculator the economy's input prices,
wages, lending rate and land rent as they stand, and `ProducerCostsMixin._cost_book` remembers the book while the economy's
prices stand. The calculator is a recorder; its own rules are in test_entry_cost_at_economy_prices. No game."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.engine import economy_cost_book as cost_book_module
from sim.engine import producer_costs
from sim.engine.making_cost import LAND_MATERIAL
from sim.engine.producer_costs import ProducerCostsMixin

CIV = {"id": "somewhere"}


def standin(prices, wage_of_trade, rent=3.5, rate=0.07):
    return types.SimpleNamespace(
        goods_market=types.SimpleNamespace(household_prices=lambda: prices),
        economy=types.SimpleNamespace(agent_wage_per_hour=wage_of_trade, agent_land_rent_per_hectare=lambda: rent),
        labour=types.SimpleNamespace(market=types.SimpleNamespace(quote=lambda trade: 9.0)),
        market_rate=lambda: rate, civ=CIV)


def recorded_arguments(sim, production=None):
    """The positional and keyword arguments `economy_cost_book` hands to `CostBook`."""
    with mock.patch.object(cost_book_module, "CostBook") as calculator:
        cost_book_module.economy_cost_book(sim, production)
    return calculator.call_args


class EconomyCostBookTests(unittest.TestCase):
    def setUp(self):
        self.call = recorded_arguments(standin({"ore_kg": 4.0, "free_kg": 0.0}, lambda trade: {"smith": 2.5}.get(trade)),
                                       production={"entry": {}})
        self.input_price_of, self.wage_of, self.rate = self.call.args

    def test_an_input_costs_the_economys_price_for_it(self):
        self.assertEqual(self.input_price_of("ore_kg"), 4.0)

    def test_an_input_with_no_price_or_a_zero_price_cannot_be_costed(self):
        self.assertIsNone(self.input_price_of("absent_kg"))
        self.assertIsNone(self.input_price_of("free_kg"))

    def test_land_is_charged_its_rent_not_a_price(self):
        self.assertIsNone(self.input_price_of(LAND_MATERIAL))
        self.assertEqual(self.call.kwargs["rent_of"](LAND_MATERIAL), 3.5)
        self.assertEqual(self.call.kwargs["rent_of"]("ore_kg"), 0.0)

    def test_a_trade_is_paid_the_economys_wage(self):
        self.assertEqual(self.wage_of("smith"), 2.5)

    def test_a_trade_the_economy_pays_nobody_is_quoted_by_the_labour_market(self):
        self.assertEqual(self.wage_of("carter"), 9.0)

    def test_the_lending_rate_civilisation_and_catalogue_are_passed_on(self):
        self.assertEqual(self.rate, 0.07)
        self.assertEqual(self.call.kwargs["civilization"], CIV)
        self.assertEqual(self.call.kwargs["production"], {"entry": {}})

    def test_no_land_rent_means_land_is_charged_nothing(self):
        call = recorded_arguments(standin({}, lambda trade: 1.0, rent=None))
        self.assertEqual(call.kwargs["rent_of"](LAND_MATERIAL), 0.0)


class CostBookMemoTests(unittest.TestCase):
    def game(self, prices, rate=0.07, year=0, techniques=None):
        game = types.SimpleNamespace(
            goods_market=types.SimpleNamespace(household_prices=lambda: prices), market_rate=lambda: rate,
            state=types.SimpleNamespace(scenario=types.SimpleNamespace(year=year)),
            techniques_in_use=lambda: techniques)
        return game

    def books(self, *games):
        """Each game's `_cost_book`, in turn on one shared cache, with the number of books built."""
        built = []
        shared = types.SimpleNamespace()
        with mock.patch.object(producer_costs, "economy_cost_book", side_effect=lambda game: built.append(game) or object()):
            for game in games:
                shared.goods_market, shared.market_rate, shared.state = game.goods_market, game.market_rate, game.state
                shared.techniques_in_use = game.techniques_in_use
                ProducerCostsMixin._cost_book(shared)
        return len(built)

    def test_the_book_is_kept_while_the_economys_prices_stand(self):
        prices, techniques = {"ore_kg": 1.0}, ("a",)
        self.assertEqual(self.books(self.game(prices, techniques=techniques), self.game(prices, techniques=techniques)), 1)

    def test_a_new_price_table_makes_a_new_book(self):
        techniques = ("a",)
        self.assertEqual(self.books(self.game({"ore_kg": 1.0}, techniques=techniques),
                                    self.game({"ore_kg": 2.0}, techniques=techniques)), 2)

    def test_a_new_year_makes_a_new_book(self):
        prices, techniques = {"ore_kg": 1.0}, ("a",)
        self.assertEqual(self.books(self.game(prices, year=0, techniques=techniques),
                                    self.game(prices, year=1, techniques=techniques)), 2)


if __name__ == "__main__":
    unittest.main()
