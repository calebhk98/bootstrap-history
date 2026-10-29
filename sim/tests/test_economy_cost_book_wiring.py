"""Complaints/507 stage 5, wiring on stand-ins: the prices module's `economy_cost_book` hands the cost calculator the economy's
input prices, wages, lending rate and land rent as they stand, and `cost_book` remembers the book while the economy's prices
stand. The calculator is a recorder; its own rules are in test_entry_cost_at_economy_prices. No game."""
QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.prices import cost_books
from sim.prices.making_cost import LAND_MATERIAL
from sim.tests import prices_stand_in

CIV = {"id": "somewhere", "starting_interest_rate": 0.05}


def module(prices, wage_of_trade, rent=3.5, rate=0.07):
    return prices_stand_in.build(civilisation=CIV, household_prices=lambda: prices, agent_wage=wage_of_trade,
                                 agent_land_rent=lambda: rent, labour_quote=lambda trade, hours=0.0: 9.0, market_rate=lambda: rate)


def recorded_arguments(prices_module):
    """The positional and keyword arguments `economy_cost_book` hands to `CostBook`."""
    with mock.patch.object(cost_books, "CostBook") as calculator:
        prices_module.economy_cost_book()
    return calculator.call_args


class EconomyCostBookTests(unittest.TestCase):
    def setUp(self):
        self.call = recorded_arguments(module({"ore_kg": 4.0, "free_kg": 0.0}, lambda trade: {"smith": 2.5}.get(trade)))
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

    def test_the_lending_rate_and_civilisation_are_passed_on(self):
        self.assertEqual(self.rate, 0.07)
        self.assertEqual(self.call.kwargs["civilization"], CIV)
        self.assertIsNone(self.call.kwargs["production"])

    def test_no_land_rent_means_land_is_charged_nothing(self):
        call = recorded_arguments(module({}, lambda trade: 1.0, rent=None))
        self.assertEqual(call.kwargs["rent_of"](LAND_MATERIAL), 0.0)


class CostBookMemoTests(unittest.TestCase):
    def books(self, *situations):
        """Each situation's `cost_book`, in turn on one module, with the number of books built."""
        built = []
        current = {}
        shared = prices_stand_in.build(household_prices=lambda: current["prices"], market_rate=lambda: current["rate"],
                                       year=lambda: current["year"], techniques_in_use=lambda: current["techniques"])
        with mock.patch.object(shared, "economy_cost_book", side_effect=lambda: built.append(1) or object()):
            for prices, rate, year, techniques in situations:
                current.update(prices=prices, rate=rate, year=year, techniques=techniques)
                shared.cost_book()
        return len(built)

    def test_the_book_is_kept_while_the_economys_prices_stand(self):
        prices, techniques = {"ore_kg": 1.0}, ("a",)
        self.assertEqual(self.books((prices, 0.07, 0, techniques), (prices, 0.07, 0, techniques)), 1)

    def test_a_new_price_table_makes_a_new_book(self):
        techniques = ("a",)
        self.assertEqual(self.books(({"ore_kg": 1.0}, 0.07, 0, techniques), ({"ore_kg": 2.0}, 0.07, 0, techniques)), 2)

    def test_a_new_year_makes_a_new_book(self):
        prices, techniques = {"ore_kg": 1.0}, ("a",)
        self.assertEqual(self.books((prices, 0.07, 0, techniques), (prices, 0.07, 1, techniques)), 2)


if __name__ == "__main__":
    unittest.main()
