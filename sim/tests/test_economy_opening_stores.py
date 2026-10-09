"""Opening stocks of durable stores of wealth: what past output leaves after loss, held by households."""

QUICK_TOPIC = True

import types as pytypes
import unittest

from sim.economy import opening_stores
from sim.economy.accounts import Book
from sim.economy.households_cohort import Cohort
from sim.economy.metal_stock import METAL_GOODS_LOSS_PER_YEAR
from sim.economy.opening import open_economy
from sim.economy.types import GoodSpec
from sim.tests import economy_fixture as fixture

GOLD = "durable_kg"
LOSS = 0.01


def setup_with(workings, gaps=None):
    return pytypes.SimpleNamespace(
        specs={GOLD: GoodSpec(GOLD, 2.0, 0.0, 100.0, "metal")},
        opening_store_output={GOLD: tuple(workings)}, opening_store_gaps=gaps or {})


def cohorts():
    return {"household:t1:0": Cohort("household:t1:0", "t1", 0, 100.0, 50.0, 0.5, last_year_income=1.0),
            "household:t1:1": Cohort("household:t1:1", "t1", 1, 100.0, 50.0, 0.5, last_year_income=3.0)}


class RetainedOutputTests(unittest.TestCase):
    def test_no_loss_keeps_all_the_output(self):
        self.assertAlmostEqual(opening_stores.retained_output(5.0, 10.0, 7.0, 0.0), 50.0)

    def test_loss_keeps_less_and_old_output_keeps_least(self):
        recent = opening_stores.retained_output(5.0, 10.0, 0.0, LOSS)
        old = opening_stores.retained_output(5.0, 10.0, 500.0, LOSS)
        self.assertLess(recent, 50.0)
        self.assertGreater(recent, old)
        self.assertGreater(old, 0.0)

    def test_each_years_output_is_lost_for_the_years_since_it_was_made(self):
        total = sum(5.0 * (1.0 - LOSS) ** age for age in range(3, 8))
        self.assertAlmostEqual(opening_stores.retained_output(5.0, 5.0, 3.0, LOSS), total)


class SeedingTests(unittest.TestCase):
    def seed(self, setup):
        record = pytypes.SimpleNamespace(book=Book(), cohorts=cohorts())
        opening_stores.seed_opening_stores(setup, record, {GOLD}, LOSS)
        return record

    def test_the_stock_is_placed_with_households_by_their_income_in_units_of_the_good(self):
        record = self.seed(setup_with([(10.0, 20.0, 0.0)]))
        poor = record.book.stock("household:t1:0", GOLD, "t1")
        rich = record.book.stock("household:t1:1", GOLD, "t1")
        kilograms = opening_stores.retained_output(10.0, 20.0, 0.0, LOSS)
        self.assertAlmostEqual((poor + rich) * 2.0, kilograms)
        self.assertAlmostEqual(rich, 3.0 * poor)

    def test_no_workings_leaves_the_households_empty(self):
        record = self.seed(setup_with([], {GOLD: "no deposit of it in the country's tiles"}))
        self.assertEqual(record.book.stock("household:t1:0", GOLD, "t1"), 0.0)

    def test_a_good_the_economy_does_not_know_is_not_seeded(self):
        setup = setup_with([(10.0, 20.0, 0.0)])
        setup.specs = {}
        record = self.seed(setup)
        self.assertEqual(record.book.stock("household:t1:0", GOLD, "t1"), 0.0)

    def test_a_good_not_fit_to_hold_as_wealth_is_not_seeded(self):
        record = pytypes.SimpleNamespace(book=Book(), cohorts=cohorts())
        opening_stores.seed_opening_stores(setup_with([(10.0, 20.0, 0.0)]), record, set(), LOSS)
        self.assertEqual(record.book.stock("household:t1:0", GOLD, "t1"), 0.0)


class OpeningEconomyTests(unittest.TestCase):
    def test_the_opened_economy_holds_the_seeded_stock_when_the_good_is_fit_to_hold(self):
        durable = fixture.specs({fixture.METAL: 20})
        setup = fixture.small_setup(specs=durable, opening_store_output={fixture.METAL: ((2.0, 100.0, 0.0),)})
        record, _areas, _carriage = open_economy(setup)
        held = sum(record.book.stock(agent, fixture.METAL, tile) for agent, cohort in record.cohorts.items()
                   for tile in [cohort.tile])
        # the seeded wealth, and besides it the stock the households keep in use (opening._seed_durable_stocks)
        self.assertGreaterEqual(held, opening_stores.retained_output(2.0, 100.0, 0.0, METAL_GOODS_LOSS_PER_YEAR))

    def test_the_opened_economy_holds_none_of_a_good_used_up_within_the_year(self):
        setup = fixture.small_setup(opening_store_output={fixture.METAL: ((2.0, 100.0, 0.0),)})
        record, _areas, _carriage = open_economy(setup)
        self.assertEqual(sum(record.book.stock(agent, fixture.METAL, cohort.tile)
                             for agent, cohort in record.cohorts.items()), 0.0)


if __name__ == "__main__":
    unittest.main()
