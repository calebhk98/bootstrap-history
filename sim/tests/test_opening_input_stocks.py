"""Complaint 473: what a producer opens holding of an input. An input another opened producer makes is bought in year
0 (producers produce and clear in input-depth order, so a user buys it before it works); an input held as well is
bought by nobody, and its maker's whole year piles up unsold (a stock the maker's plan then works off by idling).

The first test is a known failure, not a wish: the opening seeds every input for the year (`_stock_producers_with_inputs`).
Dropping the seed for inputs a maker sells the same year was built and measured on the small fixture: year 0 then trades
the input, but the dug input's cobweb moves a year earlier and two fixed-bound tests (`economy_vessel_price_fixture`,
`economy_no_offer_memory`) fail. It lands with the input-bid ceiling (Complaint 473, Update 6)."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import opening
from sim.economy.accounts import Book
from sim.economy.producers import Producer
from sim.economy.types import Recipe
from sim.tests import economy_fixture as fixture

TILE = "t"


def opened(recipes, runs):
    """(setup, record) with one producer of each recipe in `runs` working that many runs."""
    producers = {"producer:" + recipe_id: Producer("producer:" + recipe_id, "owner", recipe_id, TILE, 2.0 * count,
                                                   expected_sales=count)
                 for recipe_id, count in runs.items()}
    return types.SimpleNamespace(recipes=recipes), types.SimpleNamespace(producers=producers, book=Book())


class OpeningInputStockTests(unittest.TestCase):
    @unittest.expectedFailure
    def test_a_smelter_does_not_open_holding_ore_the_miners_sell_it_in_year_zero(self):
        setup, record = opened(fixture.recipes(), {fixture.MINE: 10.0, fixture.SMELT: 10.0})
        opening._stock_producers_with_inputs(setup, record)
        self.assertEqual(record.book.stock("producer:" + fixture.SMELT, fixture.ORE, TILE), 0.0)

    def test_an_input_nothing_opened_makes_is_held_for_the_year(self):
        setup, record = opened(fixture.recipes(), {fixture.SMELT: 10.0})
        opening._stock_producers_with_inputs(setup, record)
        wanted = 10.0 * 1000.0      # the planned runs (expected sales), not the spare capacity
        self.assertAlmostEqual(record.book.stock("producer:" + fixture.SMELT, fixture.ORE, TILE), wanted)

    def test_members_of_a_cycle_open_holding_each_others_goods(self):
        recipes = {"make_a": Recipe("make_a", {"a": 1.0}, {"b": 1.0}, {"labourer": 1.0}),
                   "make_b": Recipe("make_b", {"b": 1.0}, {"a": 1.0}, {"labourer": 1.0})}
        setup, record = opened(recipes, {"make_a": 5.0, "make_b": 5.0})
        opening._stock_producers_with_inputs(setup, record)
        self.assertGreater(record.book.stock("producer:make_a", "b", TILE), 0.0)
        self.assertGreater(record.book.stock("producer:make_b", "a", TILE), 0.0)


if __name__ == "__main__":
    unittest.main()
