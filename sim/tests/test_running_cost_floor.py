"""Complaint 135: a producer that has sunk its capital offers at its running cost, and the clearing's floor is
the share of the incumbents' cost that is running cost, both read from the recipe's own split of its cost
into running and capital parts. Build decisions keep paying back the capital (the full cost)."""

QUICK_TOPIC = True

import unittest

from sim.engine import data, entry_cost, solve_prices
from sim.engine.market_clearing import MarketClearingMixin
from sim.engine.producer_costs import ProducerCostsMixin
from sim.tests.test_capital_charge import WAGES, works_entry

RATE = 0.12


def book(production):
    civilization = dict(data.load_civ("rome_100ad"), starting_interest_rate=RATE)
    document = data.schedule_of_civilisation(civilization).document()
    return entry_cost.CostBook({"ore_kg": 1.0}, document, civilization, frozenset(), production=production)


class RunningCostSplitTests(unittest.TestCase):
    def test_the_solver_can_cost_an_entry_without_its_plant(self):
        full = solve_prices.recipe_cost_and_allocation(
            "widget_kg", works_entry(), {"ore_kg": 1.0}, WAGES, interest_rate=RATE)[1]["widget_kg"]
        running = solve_prices.recipe_cost_and_allocation(
            "widget_kg", works_entry(), {"ore_kg": 1.0}, WAGES, interest_rate=RATE,
            include_capital=False)[1]["widget_kg"]
        self.assertAlmostEqual(running, (10.0 * 1.0 + 5.0 * 1.0) / 10.0)
        self.assertGreater(full, running)

    def test_an_entry_with_no_plant_costs_the_same_either_way(self):
        entry = dict(works_entry(), capital=[])
        both = [solve_prices.recipe_cost_and_allocation(
            "widget_kg", entry, {"ore_kg": 1.0}, WAGES, include_capital=flag)[1]["widget_kg"]
            for flag in (True, False)]
        self.assertEqual(both[0], both[1])


class CostBookTests(unittest.TestCase):
    def test_running_cost_is_below_full_cost_by_the_plants_repayment(self):
        cost_book = book({"widget_kg": works_entry()})
        full = cost_book.unit_cost_hours("widget_kg", "widget_kg")
        running = cost_book.running_unit_cost_hours("widget_kg", "widget_kg")
        self.assertIsNotNone(running)
        self.assertLess(running, full)

    def test_running_share_is_one_for_an_entry_with_no_plant(self):
        cost_book = book({"widget_kg": dict(works_entry(), capital=[])})
        self.assertAlmostEqual(cost_book.running_share("widget_kg", "widget_kg"), 1.0)

    def test_running_share_is_the_running_cost_over_the_full_cost(self):
        cost_book = book({"widget_kg": works_entry()})
        share = cost_book.running_share("widget_kg", "widget_kg")
        self.assertAlmostEqual(share, cost_book.running_unit_cost_hours("widget_kg", "widget_kg")
                               / cost_book.unit_cost_hours("widget_kg", "widget_kg"))
        self.assertTrue(0.0 < share < 1.0)


class StubGame(ProducerCostsMixin, MarketClearingMixin):
    """Just enough of the engine for the cost ratios and the floor: one good made by one entry."""
    def __init__(self, entry):
        self.cost_book = book({"widget_kg": entry})
        self.memo = {}

    def _cost_book(self):
        return None, self.cost_book, self.memo

    def _reference_entry(self, material):
        return "widget_kg"

    def _material_commodity_map(self):
        return {"widget_kg": "widget"}


class OffersAndFloorTests(unittest.TestCase):
    def test_a_producer_with_its_plant_built_offers_below_the_incumbents_full_cost(self):
        game = StubGame(works_entry())
        self.assertLess(game.entry_cost_ratio("widget_kg", "widget_kg", running=True), 1.0)
        self.assertAlmostEqual(game.entry_cost_ratio("widget_kg", "widget_kg"), 1.0)

    def test_the_floor_is_the_running_share_of_the_incumbents_cost(self):
        game = StubGame(works_entry())
        share = game.commodity_floor_ratio("widget")
        self.assertTrue(0.0 < share < 1.0)
        self.assertAlmostEqual(share, game.entry_cost_ratio("widget_kg", "widget_kg", running=True))
        self.assertAlmostEqual(game._floor_ratio("widget"), share)

    def test_a_commodity_nothing_can_split_sells_at_no_less_than_its_cost(self):
        game = StubGame(works_entry())
        self.assertAlmostEqual(game._floor_ratio("unknown"), 1.0)


if __name__ == "__main__":
    unittest.main()
