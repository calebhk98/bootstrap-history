"""Plant building and plant bids (sim/economy/economy.py): bids have a derived ceiling, building keeps the
goods it did not use, and following the engine keeps the other fields of a record."""
import types as pytypes
import unittest
from unittest import mock

from sim.economy import economy, producers, unit_cost
from sim.economy.accounts import Book
from sim.economy.economy import Economy
from sim.economy.households_cohort import Cohort
from sim.economy.types import EDGE_ISSUE, EDGE_PRODUCTION, GoodsMove, Transfer

RECIPE = pytypes.SimpleNamespace(plant_goods={"iron": 2.0, "wood": 10.0}, plant_life_years=20.0)


def economy_of():
    """An Economy with only the pieces the plant methods read."""
    self = object.__new__(Economy)
    self.setup = pytypes.SimpleNamespace(recipes={"recipe": RECIPE}, currency_id="coin")
    self.record = pytypes.SimpleNamespace(book=Book(), producers={"mill": producers.Producer("mill", "owner", "recipe", "t1", 1.0)},
                                          cohorts={}, workforce={}, worn_runs={"mill": 1.0})
    self.area_map = pytypes.SimpleNamespace(goods=lambda: ("iron", "wood"))
    return self


class PlantBuildingTests(unittest.TestCase):
    def test_goods_beyond_what_the_built_capacity_uses_stay_in_stock(self):
        built = economy_of()
        book = built.record.book
        book.move_many([GoodsMove(EDGE_PRODUCTION, "mill", "iron", "t1", 2.0, "bought"),
                        GoodsMove(EDGE_PRODUCTION, "mill", "wood", "t1", 5.0, "bought")])
        built._build_plant({"mill": 1.0})
        self.assertAlmostEqual(built.record.producers["mill"].capacity_runs, 1.5)
        self.assertAlmostEqual(book.stock("mill", "wood", "t1"), 0.0)
        self.assertAlmostEqual(book.stock("mill", "iron", "t1"), 1.0)


class PlantBidCeilingTests(unittest.TestCase):
    def rebuild_ceiling(self, rate):
        rebuilding = economy_of()
        rebuilding.record.book.transfer(Transfer(EDGE_ISSUE, "mill", "coin", 100.0, "cash"))
        view = pytypes.SimpleNamespace(interest_rate=lambda money: rate, area_of=lambda good, tile: "area",
                                       price=lambda good, area: 1.0)
        order_book = {}
        with mock.patch.object(producers, "live_input_prices", return_value={}), \
                mock.patch.object(producers, "live_wages", return_value={}), \
                mock.patch.object(producers, "expected_output_prices", return_value={}), \
                mock.patch.object(unit_cost, "return_on_capital", return_value=0.5):
            rebuilding._rebuild_worn_plant(view, order_book)
        return order_book[("iron", "area")][0][0].maximum_price

    def test_a_near_zero_rate_does_not_lift_the_ceiling_without_limit(self):
        # earning half the price a year for the plant's life is worth that many halves, no more
        self.assertLessEqual(self.rebuild_ceiling(0.0), 0.5 * RECIPE.plant_life_years + 1e-9)

    def test_the_ceiling_falls_as_the_rate_rises(self):
        self.assertGreater(self.rebuild_ceiling(0.01), self.rebuild_ceiling(0.2))

    def test_worth_over_the_plants_life_is_an_annuity(self):
        self.assertAlmostEqual(economy.plant_worth_ratio(0.5, 0.0, 20.0), 10.0)
        self.assertAlmostEqual(economy.plant_worth_ratio(1.0, 0.1, 2.0), 1 / 1.1 + 1 / 1.21)
        self.assertEqual(economy.plant_worth_ratio(1.0, 0.1, 0.0), 1.0)


class FollowTests(unittest.TestCase):
    def test_following_yields_and_population_keep_the_other_fields(self):
        following = economy_of()
        following.record.producers["mill"] = producers.Producer("mill", "owner", "recipe", "t1", 3.0, years_of_loss=2)
        following._follow_yields(pytypes.SimpleNamespace(yield_factor_by_producer={"mill": 0.5}))
        mill = following.record.producers["mill"]
        self.assertEqual((mill.yield_factor, mill.years_of_loss), (0.5, 2))
        following.record.cohorts["c"] = Cohort("c", "t1", 0, 10.0, 5.0, 1.0)
        following._follow_population(pytypes.SimpleNamespace(population_by_tile={"t1": 20.0}))
        cohort = following.record.cohorts["c"]
        self.assertEqual((cohort.people, cohort.working_people), (20.0, 10.0))


if __name__ == "__main__":
    unittest.main()
