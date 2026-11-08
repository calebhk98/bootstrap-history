"""The labour offers table and its kernels give what the closures of `HourSupply` gave, on written-out rows."""
QUICK_TOPIC = True

import unittest

import numpy

from sim.economy import household_hours_year
from sim.economy.labour_offers_kernels import offer_matrix, settle_offers, whole_hours_by_cohort
from sim.economy.labour_offers_table import LABOUR_OFFERS, LabourOffers, PlotParameters, build_labour_offers, labour_ids, market_ranks
from sim.economy.labour_supply import HourSupply
from sim.economy.labour_supply_markets import MarketHours
from sim.economy.types import LabourOffer
from sim.labour.api import sold_hours_range
from sim.labour.market import clearing_arrays
from sim.labour.market.records import YearInputs

EXPONENT = 3.0
WAGES = (-1.0, 0.0, 0.05, 0.7, 2.0, 50.0)

# cohort "a" holds three offers (one with no hours) and a plot; "b" two; "c" has one offer with no hours
OFFERS = [LabourOffer("a", "reaper", "vale", 600.0, 0.1), LabourOffer("a", "smith", "vale", 400.0, 0.2),
          LabourOffer("b", "reaper", "vale", 900.0, 0.1), LabourOffer("a", "reaper", "hill", 0.0, 0.1),
          LabourOffer("c", "smith", "hill", 0.0, 0.3), LabourOffer("b", "smith", "hill", 250.0, 0.4)]
PLOT_A = PlotParameters(500.0, 2.0, 300.0, 2.0)
MARKETS = [("reaper", "hill"), ("reaper", "vale"), ("smith", "hill"), ("smith", "vale")]


def table():
    """OFFERS as rows, numbered by hand: cohorts a, b, c = 0, 1, 2; markets in sorted (trade, area) order as MARKETS."""
    return LABOUR_OFFERS.table_of(
        LabourOffers, cohort=[0, 0, 1, 0, 2, 1], trade=[0, 1, 0, 0, 1, 1], area=[1, 1, 1, 0, 0, 0], market=[1, 3, 1, 0, 2, 2],
        hours=[600.0, 400.0, 900.0, 0.0, 0.0, 250.0], reservation_wage=[0.1, 0.2, 0.1, 0.1, 0.3, 0.4],
        whole_hours=[1000.0, 1000.0, 1150.0, 1000.0, 0.0, 1150.0], plan_hours=[100.0, 100.0, 40.0, 100.0, 0.0, 40.0],
        work_hours=[50.0, 50.0, 700.0, 50.0, 0.0, 700.0], has_plot=[True, True, False, True, False, False],
        plot_hours_per_worker=[500.0, 500.0, 0.0, 500.0, 0.0, 0.0], marginal_return=[2.0, 2.0, 0.0, 2.0, 0.0, 0.0],
        usable_per_worker=[300.0, 300.0, 0.0, 300.0, 0.0, 0.0], workers=[2.0, 2.0, 0.0, 2.0, 0.0, 0.0],
        sold_hours=numpy.zeros(6), kept_hours=numpy.zeros(6))


def reference():
    """The closures the table replaces: the supply's offer-by-offer rule over the same offers."""
    return HourSupply(offers=OFFERS, plan_hours={"a": 100.0, "b": 40.0}, work_hours={"a": 50.0, "b": 700.0},
                      plot_hours_at={"a": household_hours_year.plot_schedule(*PLOT_A)})


class WholeHours(unittest.TestCase):
    def test_a_cohorts_hours_are_added_over_its_offers(self):
        self.assertEqual(whole_hours_by_cohort(table(), 3).tolist(), [1000.0, 1150.0, 0.0])


class OfferMatrix(unittest.TestCase):
    def test_columns_are_the_offers_with_hours_grouped_by_market_in_row_order(self):
        matrix, first, last = offer_matrix(table(), 4)
        self.assertEqual((first.tolist(), last.tolist()), ([0, 0, 2, 3], [0, 2, 3, 4]))
        self.assertEqual(matrix[0].tolist(), [600.0, 900.0, 250.0, 400.0])        # OFFER_HOURS

    def test_hours_sold_at_a_wage_are_the_closures_hours_for_each_market(self):
        held = reference()
        matrix, first, last = offer_matrix(table(), 4)
        for market, (trade, area) in enumerate(MARKETS):
            closure = held.hours_at(trade, area)
            for wage in WAGES:
                self.assertEqual(sold_hours_range(wage, matrix, EXPONENT, first[market], last[market]), closure(wage))

    def test_a_cohort_with_no_hours_in_all_sells_nothing(self):
        rows = table()
        rows.whole_hours[2] = 0.0                                   # cohort b: its offer in reaper/vale becomes a zero column
        matrix, first, last = offer_matrix(rows, 4)
        self.assertEqual(matrix[0, first[1]:last[1]].tolist(), [600.0, 0.0])
        self.assertEqual(sold_hours_range(1.0, matrix, EXPONENT, first[1], last[1]), reference().sold_hours_schedule(OFFERS[0])(1.0))


class Settle(unittest.TestCase):
    def test_sold_and_kept_hours_are_the_splits_at_each_markets_wage(self):
        held = reference()
        rows = table()
        market_wage, known = numpy.array([0.0, 0.7, 2.0, 0.0]), numpy.array([False, True, True, False])
        kept_by_cohort = settle_offers(rows, market_wage, known, EXPONENT, 3)
        wages = [0.7, 0.2, 0.7, 0.1, 2.0, 2.0]       # smith/vale and reaper/hill are not known: each offer's own reservation wage
        for row, offer in enumerate(OFFERS):
            sold, _home = held.split(offer, wages[row])
            self.assertEqual(rows.sold_hours[row], sold)
            self.assertEqual(rows.kept_hours[row], offer.hours - sold)
        self.assertEqual(kept_by_cohort.tolist(), [rows.kept_hours[0] + rows.kept_hours[1] + rows.kept_hours[3],
                                                   rows.kept_hours[2] + rows.kept_hours[5], rows.kept_hours[4]])


class BuildTable(unittest.TestCase):
    def test_markets_are_ranked_by_trade_then_area(self):
        market, market_trade, market_area = market_ranks(numpy.array([1, 0, 1, 0]), numpy.array([0, 1, 0, 0]), 2)
        self.assertEqual((market.tolist(), market_trade.tolist(), market_area.tolist()), ([2, 1, 2, 0], [0, 0, 1], [0, 1, 0]))

    def test_ids_are_numbered_in_sorted_order_and_the_cohort_figures_are_copied_to_its_rows(self):
        rows, ids, markets = build_labour_offers(OFFERS, {"a": 100.0, "b": 40.0}, {"a": 50.0, "b": 700.0}, {"a": PLOT_A})
        self.assertEqual((ids.cohorts.names, ids.trades.names, ids.areas.names), (("a", "b", "c"), ("reaper", "smith"), ("hill", "vale")))
        expected = table()
        for column in LABOUR_OFFERS.columns:
            self.assertEqual(getattr(rows, column.name).tolist(), getattr(expected, column.name).tolist(), column.name)
        self.assertEqual(ids.market_names(markets.trade_of_market, markets.area_of_market), MARKETS)

    def test_a_cohort_with_figures_but_no_offer_is_numbered(self):
        self.assertEqual(labour_ids(OFFERS, ["z"]).cohorts.names, ("a", "b", "c", "z"))


class TheSupplyOnTheTable(unittest.TestCase):
    def test_parameters_without_closures_give_the_closures_schedules_and_settlement(self):
        closures = reference()
        numbers = HourSupply(OFFERS, {"a": 100.0, "b": 40.0}, {"a": 50.0, "b": 700.0}, {}, plot_parameters={"a": PLOT_A})
        for market, schedule in numbers.schedules().items():
            for wage in WAGES:
                self.assertEqual(schedule(wage), closures.hours_at(*market)(wage))
        cleared = {("reaper", "vale"): 0.7}
        self.assertEqual([offer.hours for offer in numbers.settle(cleared)], [offer.hours for offer in closures.settle(cleared)])
        self.assertEqual(numbers.kept, closures.kept)
        self.assertEqual(list(numbers.kept), list(closures.kept))

    def test_the_table_schedule_is_read_by_the_clearing_arrays_and_a_replaced_schedule_turns_that_off(self):
        schedules = HourSupply(OFFERS, {}, {}, {}).schedules()
        self.assertIsInstance(schedules, MarketHours)
        inputs = YearInputs(trades={}, bids=[], subsistence_per_worker_year={}, hours_per_worker_year=1.0, discount_rate=0.0,
                            career_years=1.0, hours_sold_at=schedules)
        self.assertTrue(clearing_arrays.kernel_applies(inputs))
        schedules[("reaper", "vale")] = lambda wage: 5.0
        self.assertFalse(clearing_arrays.kernel_applies(inputs))
        self.assertEqual(schedules[("reaper", "vale")](1.0), 5.0)

    def test_a_bare_plot_function_keeps_the_plain_path(self):
        supply = HourSupply(OFFERS, {}, {}, {"a": lambda wage: 40.0})
        self.assertNotIsInstance(supply.schedules(), MarketHours)
        self.assertEqual(supply.hours_at("reaper", "vale")(1.0), (600.0 - 40.0 * 600.0 / 1000.0) + 900.0)


if __name__ == "__main__":
    unittest.main()
