"""Rent in a run's cost: it slows planning, entry and expansion where land is short, and changes nothing at zero."""
import unittest

from sim.economy import entry, producers, unit_cost
from sim.economy.accounts import Book
from sim.economy.market_memory import MarketMemory
from sim.economy.record import EconomyRecord
from sim.economy.types import CurrencySpec, Recipe
from sim.tests.test_economy_producers import FARM, View, farm_view, farmer


class UnitCostRentTests(unittest.TestCase):
    prices, wages = {"seed": 1.0}, {"hand": 1.0}

    def test_rent_adds_to_the_variable_cost_of_a_run(self):
        base = unit_cost.variable_cost_per_run(FARM, self.prices, self.wages)
        self.assertAlmostEqual(unit_cost.variable_cost_per_run(FARM, self.prices, self.wages, rent=3.0), base + 3.0)

    def test_no_rent_leaves_every_figure_as_it_was(self):
        revenue = {"grain": 1.0}
        self.assertEqual(unit_cost.return_on_capital(FARM, revenue, self.prices, self.wages),
                         unit_cost.return_on_capital(FARM, revenue, self.prices, self.wages, rent=0.0))
        self.assertEqual(unit_cost.expected_margin(FARM, revenue, self.prices, self.wages, 0.05),
                         unit_cost.expected_margin(FARM, revenue, self.prices, self.wages, 0.05, rent=0.0))

    def test_rent_lowers_the_return_and_the_margin(self):
        revenue = {"grain": 2.0}
        self.assertLess(unit_cost.return_on_capital(FARM, revenue, self.prices, self.wages, rent=2.0),
                        unit_cost.return_on_capital(FARM, revenue, self.prices, self.wages))
        self.assertAlmostEqual(unit_cost.expected_margin(FARM, revenue, self.prices, self.wages, 0.05, rent=2.0),
                               unit_cost.expected_margin(FARM, revenue, self.prices, self.wages, 0.05) - 2.0)


class PlanRentTests(unittest.TestCase):
    def test_a_producer_whose_land_rent_eats_the_margin_works_less(self):
        view = farm_view(1.6)                       # revenue 16 against cost 7
        free = producers.plan(farmer(), FARM, view, 1000.0)
        paying = producers.plan(farmer(land_rent_per_run=8.0), FARM, view, 1000.0)
        self.assertLess(paying.runs, free.runs)

    def test_runs_never_exceed_the_land_it_was_granted(self):
        plan = producers.plan(farmer(land_run_cap=2.0), FARM, farm_view(5.0), 1000.0)
        self.assertLessEqual(plan.runs, 2.0 + 1e-9)
        self.assertGreater(plan.wanted_runs, 2.0)         # what it asked for is kept for the land market

    def test_without_rent_or_cap_the_plan_is_unchanged(self):
        view = farm_view(5.0)
        self.assertEqual(producers.plan(farmer(), FARM, view, 1000.0),
                         producers.plan(farmer(land_rent_per_run=0.0, land_run_cap=-1.0), FARM, view, 1000.0))


class EntryRentTests(unittest.TestCase):
    SALT = Recipe("boil_salt", {"salt": 10.0}, {"firewood": 5.0}, {"hand": 2.0}, {"pan": 1.0}, {}, 10.0)

    def plans(self, rent_by_tile):
        view = View(prices={"salt": 1.0, "firewood": 0.1, "pan": 2.0}, wages={"hand": 0.2})
        unmet = {("salt", "area"): entry.UnmetDemand("salt", "area", "anchor", 100.0)}
        return entry.entry_plans({"boil_salt": self.SALT}, view, unmet, rent_by_tile, {"boil_salt": 1.0})

    def test_entry_slows_where_land_is_dear(self):
        self.assertEqual(len(self.plans({})), 1)
        self.assertEqual(len(self.plans({"anchor": 1.0})), 1)
        self.assertEqual(self.plans({"anchor": 50.0}), [])

    def test_the_planned_return_falls_with_rent(self):
        self.assertLess(self.plans({"anchor": 1.0})[0].yearly_return, self.plans({})[0].yearly_return)


class RecordTests(unittest.TestCase):
    def test_last_years_rent_round_trips_through_the_save(self):
        source = EconomyRecord(book=Book(), memory=MarketMemory(), currency=CurrencySpec("coin", "fiat", None, 0.0, None))
        source.land_rent = {"t": 1.5}
        self.assertEqual(EconomyRecord.from_record(source.to_record()).land_rent, {"t": 1.5})


if __name__ == "__main__":
    unittest.main()
