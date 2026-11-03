"""Sweep 2 labour fixes, each rule called on values written out here: the unskilled option and the substitute wage
read the wages of the year's start; a missing outside option is None, not zero; a teacher that is no trade is
refused; the staff ceiling reports its scale without writing it anywhere; places posted count as people held."""
QUICK_TOPIC = True

import types
import unittest

from sim.labour.labour_capacity import Capacity
from sim.labour.market import clearing, expectations, reservation, trades
from sim.labour.market.records import EmployerHoursBid, MarketState, YearInputs
from sim.labour.request_rules import source_trade_unusable
from sim.labour.staff_book import StaffBook

SPECS = trades.trade_specs({"digger": {"family": "earth", "training_years": 0},
                            "aaa": {"family": "care", "training_years": 5},
                            "zzz": {"family": "care", "training_years": 5}})


def inputs(subsistence=None, bids=()):
    return YearInputs(trades=SPECS, bids=list(bids), subsistence_per_worker_year={"vale": 100.0} if subsistence is None else subsistence,
                      hours_per_worker_year=100.0, discount_rate=0.03, career_years=30.0)


class StartOfYearWages(unittest.TestCase):
    def test_the_unskilled_option_is_the_start_wage_given_and_none_for_the_unskilled_trade_itself(self):
        self.assertEqual(clearing.unskilled_option({"vale": {"digger": 2.5}}, inputs(), "vale", "aaa"), 2.5)
        self.assertIsNone(clearing.unskilled_option({"vale": {"digger": 2.5}}, inputs(), "vale", "digger"))

    def test_an_area_that_paid_no_unskilled_wage_has_no_option_not_a_zero_one(self):
        self.assertIsNone(clearing.unskilled_option({}, inputs(), "vale", "aaa"))

    def test_the_substitute_wage_is_the_start_unskilled_wage_times_the_premium_and_none_with_no_figure_at_all(self):
        with_wage = clearing.trained_substitute_wage({"vale": {"digger": 3.0}}, inputs(), "vale", "aaa")
        none_known = clearing.trained_substitute_wage({}, inputs({}), "vale", "aaa")
        self.assertGreater(with_wage, 3.0)
        self.assertIsNone(none_known)

    def test_two_skilled_trades_cleared_in_either_name_order_see_the_same_unskilled_wage(self):
        state = MarketState(workers={"vale": {"digger": [50.0, 0, 0, 0, 0], "aaa": [10.0, 0, 0, 0, 0], "zzz": [10.0, 0, 0, 0, 0]}})
        state.wages = {"vale": {"digger": 1.0, "aaa": 1.0, "zzz": 1.0}}
        bids = [EmployerHoursBid("e", "digger", "vale", 9000.0, 20.0)]      # the unskilled wage rises this year
        results = {each.trade: each for each in clearing.clear_all(state, inputs(bids=bids))}
        self.assertGreater(results["digger"].wage, 1.0)
        self.assertEqual(results["aaa"].wage, results["zzz"].wage)


class MissingOutsideOption(unittest.TestCase):
    def test_no_stated_subsistence_gives_no_reservation_wage(self):
        self.assertIsNone(reservation.reservation_wage(inputs({}), "vale", 0.0))

    def test_no_stated_subsistence_gives_no_expected_income_and_no_income_at_graduation(self):
        self.assertIsNone(expectations.expected_income(MarketState(), inputs({}), {}, "vale", "aaa"))
        self.assertIsNone(expectations.income_at_graduation(MarketState(), inputs({}), {}, "vale", "aaa", [1.0]))

    def test_an_area_with_no_stated_subsistence_holds_no_market(self):
        state = MarketState(workers={"vale": {"aaa": [10.0, 0, 0, 0, 0]}})
        self.assertIsNone(clearing.clear_one(state, inputs({}), "aaa", "vale", []))
        self.assertEqual(clearing.clear_all(state, inputs({})), [])


class Teachers(unittest.TestCase):
    def test_a_source_that_is_no_trade_cannot_teach(self):
        self.assertTrue(source_trade_unusable("nonesuch", {"smith": 1.0}, set(), set()))

    def test_an_absent_source_cannot_teach_unless_it_was_taught_into_being(self):
        self.assertTrue(source_trade_unusable("smith", {"smith": 1.0}, {"smith"}, set()))
        self.assertFalse(source_trade_unusable("smith", {"smith": 1.0}, {"smith"}, {"smith"}))


class StaffCeiling(unittest.TestCase):
    def capacity(self):
        world = types.SimpleNamespace()      # no commands: a write through the world would raise
        capacity = Capacity(world, book=None, market=None, schedule=None, trades=None)
        capacity._institutional_load = lambda with_directors=False: (2.0, 6.0, 1.0)
        capacity._staffing_affordability = lambda: (4.0, 1.0)
        capacity.supervision_room = lambda: 3.0
        return capacity

    def test_the_ceiling_reports_its_scale_and_the_capacity_is_the_same_three_ceilings(self):
        capacity = self.capacity()
        scholars, artisans, directors, scale = capacity.staff_ceiling()
        self.assertEqual(capacity.staff_capacity(), (scholars, artisans, directors))
        self.assertAlmostEqual(scale, 4.0 / (8.0 + 3.0 * capacity.STAFF_EXTRA_HEADROOM_WEIGHT))


class PostedPlaces(unittest.TestCase):
    def book(self, employed, wanted):
        book = StaffBook(types.SimpleNamespace(workforce=types.SimpleNamespace(staff_wanted={"smith": wanted}, training=[])))
        book.employed = lambda trade: employed
        return book

    def test_places_posted_beyond_the_people_employed_count_as_held(self):
        self.assertEqual(self.book(2.0, 5.0).employed_or_posted("smith"), 5.0)
        self.assertEqual(self.book(4.0, 1.0).employed_or_posted("smith"), 4.0)


if __name__ == "__main__":
    unittest.main()
