"""The opening's durable stock is a fixed point of buying, use and year-end losses."""

QUICK_TOPIC = True

import unittest

from sim.economy import durable_stock, inventory, opening
from sim.economy.accounts import Book
from sim.economy.market_memory import MarketMemory
from sim.economy.record import EconomyRecord
from sim.economy.households_orders import _durable_ratio
from sim.economy.types import GoodSpec
from sim.tests.economy_fixture import small_setup
from sim.tests.test_economy_households import BASKET, SPECS, View, cohort


class DurableStationaryTests(unittest.TestCase):
    def test_opening_sizing_and_seeded_household_orders_agree_on_replacement(self):
        household = cohort(last_year_income=30000.0)
        setup = small_setup(basket=BASKET, specs=SPECS)
        record = EconomyRecord(Book(), MarketMemory(), setup.currency,
                               cohorts={household.agent_id: household},
                               titles={household.tile: {household.agent_id: 1.0}})
        view = View()
        view.stock = record.book.stock
        before = list(opening._opening_bids(setup, record, view))
        opening._seed_durable_stocks(setup, record, view)
        after = list(opening._opening_bids(setup, record, view, stationary_durables=False))
        wanted = next(bid for _, bid, _ in before if bid.good == "plough")
        ordered = next(bid for _, bid, _ in after if bid.good == "plough")
        self.assertGreater(wanted.flexible_quantity, 0.0)
        self.assertAlmostEqual(wanted.flexible_quantity, ordered.flexible_quantity)
        self.assertAlmostEqual(wanted.budget, ordered.budget)
        self.assertAlmostEqual(record.book.stock(household.agent_id, "plough", household.tile),
                               wanted.flexible_quantity * (SPECS["plough"].service_life_years - 1.0))

    def test_buying_then_year_end_losses_returns_the_solved_stock(self):
        for life, spoilage in ((1.0, 0.0), (4.0, 0.0), (20.0, 0.02), (100.0, 0.001)):
            with self.subTest(life=life, spoilage=spoilage):
                spec = GoodSpec("tool", 1.0, spoilage, life, "tool")
                flow = 10.0
                serving = flow * life
                opening = durable_stock.after_year_end_losses(serving, spec)
                bought = flow * _durable_ratio("tool", flow, opening, {"tool": spec})
                self.assertAlmostEqual(opening + bought, serving)
                holdings = {("household", "tool", "tile"): opening + bought}
                lost = sum(move.quantity for move in inventory.wear_moves(holdings, {"tool": spec}, {"household"}))
                lost += sum(move.quantity for move in inventory.spoilage_moves(holdings, {"tool": spec}))
                self.assertAlmostEqual(opening + bought - lost, opening)
                self.assertAlmostEqual(bought, durable_stock.replacement_for_flow(flow, spec))

    def test_serving_stock_does_not_buy_wear_that_has_not_happened(self):
        spec = GoodSpec("tool", 1.0, 0.0, 10.0, "tool")
        self.assertEqual(_durable_ratio("tool", 10.0, 100.0, {"tool": spec}), 0.0)

    def test_shortage_is_filled_to_the_serving_stock_without_a_second_wear_allowance(self):
        spec = GoodSpec("tool", 1.0, 0.0, 4.0, "tool")
        self.assertEqual(_durable_ratio("tool", 10.0, 20.0, {"tool": spec}), 2.0)


if __name__ == "__main__":
    unittest.main()
