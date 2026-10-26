"""Complaints/507 stage 5: what an entry costs a producer is the calculator at the economy's prices, wages, rate and rent.
A plant that exists offers at its running cost, a new one is judged at its full cost, and the cost moves with the economy's
input prices and wages (not with the long-run table). `CostBook` is called with price and wage functions the test builds,
and the prices module's `entry_cost_ratio` on a stand-in; the cost book a game builds from the economy's prices is
`test_economy_cost_book_wiring`."""
QUICK_TOPIC = True

import unittest

from sim.prices import entry_cost
from sim.tests import prices_stand_in
from sim.tests.test_capital_charge import works_entry

RATE = 0.12
ENTRY = "widget_kg"


def book(ore_price=1.0, wage=1.0, rate=RATE, entry=None):
    return entry_cost.CostBook({"ore_kg": ore_price}.get, {"labourer": wage}.get, rate,
                               production={ENTRY: entry or works_entry()})


def stub_game(cost_book):
    """One good made by one entry, the incumbents' own."""
    return prices_stand_in.build_over_book(cost_book, ENTRY)


class CostAtEconomyPricesTests(unittest.TestCase):
    def test_a_plant_that_exists_offers_at_its_running_cost_below_the_full_cost(self):
        cost_book = book()
        running, full = cost_book.running_unit_cost(ENTRY, ENTRY), cost_book.unit_cost(ENTRY, ENTRY)
        self.assertTrue(0.0 < running < full)

    def test_dearer_inputs_at_the_economy_raise_the_cost_of_making(self):
        self.assertGreater(book(ore_price=2.0).unit_cost(ENTRY, ENTRY), book().unit_cost(ENTRY, ENTRY))

    def test_dearer_inputs_raise_the_running_cost_too(self):
        self.assertGreater(book(ore_price=2.0).running_unit_cost(ENTRY, ENTRY), book().running_unit_cost(ENTRY, ENTRY))

    def test_dearer_wages_at_the_economy_raise_the_cost_of_making(self):
        self.assertGreater(book(wage=2.0).unit_cost(ENTRY, ENTRY), book().unit_cost(ENTRY, ENTRY))

    def test_a_dearer_rate_raises_the_full_cost_and_leaves_the_running_cost_alone(self):
        cheap, dear = book(rate=0.05), book(rate=0.20)
        self.assertGreater(dear.unit_cost(ENTRY, ENTRY), cheap.unit_cost(ENTRY, ENTRY))
        self.assertAlmostEqual(dear.running_unit_cost(ENTRY, ENTRY), cheap.running_unit_cost(ENTRY, ENTRY))

    def test_an_input_with_no_price_cannot_be_costed(self):
        priceless = entry_cost.CostBook({}.get, {"labourer": 1.0}.get, RATE, production={ENTRY: works_entry()})
        self.assertIsNone(priceless.unit_cost(ENTRY, ENTRY))


class EntryCostRatioTests(unittest.TestCase):
    def test_the_incumbents_own_entry_costs_the_same_as_itself(self):
        self.assertAlmostEqual(stub_game(book()).entry_cost_ratio(ENTRY, ENTRY), 1.0)

    def test_its_running_ratio_is_the_running_cost_over_the_full_cost(self):
        cost_book = book()
        ratio = stub_game(cost_book).entry_cost_ratio(ENTRY, ENTRY, running=True)
        self.assertLess(ratio, 1.0)
        self.assertAlmostEqual(ratio, cost_book.running_unit_cost(ENTRY, ENTRY) / cost_book.unit_cost(ENTRY, ENTRY))


if __name__ == "__main__":
    unittest.main()
