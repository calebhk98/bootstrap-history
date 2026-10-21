"""A scarce skilled trade pays more than its long-run training cost this year (Complaint 678): trainees take years to
arrive, so the cost of training a substitute caps what entrants expect after training, not today's wage. Today's wage is
bounded by the bid-weighted worth of the hours wanted and by the cost of fetching trained hands. Plain records, no game."""

QUICK_TOPIC = True

import unittest

from sim.labour.market import clearing, expectations, scarcity, trades
from sim.labour.market.import_cost import ImportCosts
from sim.labour.market.records import Bid, MarketState, Route, YearInputs

SPECS = trades.trade_specs({"digger": {"family": "earth", "training_years": 0},
                            "healer": {"family": "care", "training_years": 5}})
HOURS = 100.0
DISCOUNT = 0.03
CAREER = 30.0
WHOLE_BAND = [1.0, 1.0, 1.0, 1.0, 1.0]


def inputs(bids, routes=None, hours_share_at=None):
    return YearInputs(trades=SPECS, bids=bids, subsistence_per_worker_year={"vale": 100.0, "hill": 100.0},
                      hours_per_worker_year=HOURS, discount_rate=DISCOUNT, career_years=CAREER,
                      routes=routes or {}, hours_share_at=hours_share_at or {})


def state(healers, hill_healers=0.0):
    held = MarketState(workers={"vale": {"digger": [50.0, 0.0, 0.0, 0.0, 0.0],
                                         "healer": [healers, 0.0, 0.0, 0.0, 0.0]}})
    held.wages = {"vale": {"digger": 1.0, "healer": 1.0}}
    if hill_healers:
        held.workers["hill"] = {"healer": [hill_healers, 0.0, 0.0, 0.0, 0.0]}
        held.wages["hill"] = {"healer": 1.2}
    return held


def hungry(maximum=500.0, hours=5000.0):
    return Bid("clinic", "healer", "vale", hours, maximum)


def settle(held, year_inputs, years=40):
    result = None
    for _year in range(years):
        result = [each for each in clearing.clear_all(held, year_inputs)
                  if each.trade == "healer" and each.area == "vale"][0]
    return result


def long_run_cap(held, year_inputs):
    return clearing.trained_substitute_wage(held, year_inputs, "vale", "healer")


class TodaysWageClearsAgainstBids(unittest.TestCase):

    def test_a_thin_trade_with_bids_far_above_the_long_run_cap_pays_above_it(self):
        held, year_inputs = state(healers=1.0), inputs([hungry()])
        result = settle(held, year_inputs)
        self.assertGreater(result.wage, 2.0 * long_run_cap(held, year_inputs))

    def test_the_wage_never_exceeds_the_most_an_employer_will_pay(self):
        result = settle(state(healers=1.0), inputs([hungry(maximum=3.0)]))
        self.assertLessEqual(result.wage, 3.0 + 1e-9)

    def test_one_stray_bid_with_few_hours_does_not_set_the_wage(self):
        stray = Bid("fool", "healer", "vale", 1.0, 1e6)
        result = settle(state(healers=1.0), inputs([hungry(maximum=5.0), stray]))
        self.assertLess(result.wage, 5.1)

    def test_a_trade_needing_no_training_stays_at_the_long_run_cost(self):
        specs = trades.trade_specs({"digger": {"family": "earth", "training_years": 0, "fallback": True},
                                    "reaper": {"family": "earth", "training_years": 0}})
        held = MarketState(workers={"vale": {"digger": [50.0, 0.0, 0.0, 0.0, 0.0], "reaper": [1.0, 0.0, 0.0, 0.0, 0.0]}})
        held.wages = {"vale": {"digger": 1.0, "reaper": 1.0}}
        bids = [Bid("farm", "reaper", "vale", 5000.0, 50.0), Bid("pit", "digger", "vale", 99999.0, 1.0)]
        year_inputs = YearInputs(trades=specs, bids=bids, subsistence_per_worker_year={"vale": 100.0},
                                 hours_per_worker_year=HOURS, discount_rate=DISCOUNT, career_years=CAREER)
        for _year in range(40):
            cleared = clearing.clear_all(held, year_inputs)
        reaper = [each for each in cleared if each.trade == "reaper"][0]
        self.assertLessEqual(reaper.wage, held.wages["vale"]["digger"] + 1e-9)


class FetchingTrainedHandsBoundsTheWage(unittest.TestCase):

    def test_the_wage_stops_at_the_cost_of_bringing_trained_hands_in(self):
        held = state(healers=1.0, hill_healers=5000.0)
        year_inputs = inputs([hungry(hours=HOURS * 3000.0)], routes={"vale": [Route("hill", 20.0)]})
        fetch = ImportCosts(held, year_inputs).wage("vale", "healer")
        result = settle(held, year_inputs, years=1)
        self.assertIsNotNone(fetch)
        self.assertLessEqual(result.wage, fetch + 1e-9)


class OwnWorkersOfferMoreHoursAtTheScarcityWage(unittest.TestCase):

    def test_hours_sold_rise_with_the_wage_past_the_long_run_cap(self):
        def share(wage):
            return min(1.0, 0.5 * wage / 2.0)
        held = state(healers=10.0)
        year_inputs = inputs([hungry()], hours_share_at={("healer", "vale"): share})
        cap = long_run_cap(held, year_inputs)
        result = settle(held, year_inputs)
        self.assertGreater(result.wage, cap)
        self.assertGreater(result.hours_offered, 10.0 * HOURS * share(cap))


class EntrantsExpectTheLongRunCap(unittest.TestCase):

    def test_graduation_income_stays_at_the_cap_while_today_pays_more(self):
        held = state(healers=1.0)
        year_inputs = inputs([hungry()])
        cap = long_run_cap(held, year_inputs)
        result = settle(held, year_inputs)
        reservation = clearing.reservation_wage(year_inputs, "vale", SPECS["healer"].fatality_risk_per_year)
        expected = expectations.income_at_graduation(held, year_inputs, {("vale", "healer"): result}, "vale", "healer", WHOLE_BAND)
        self.assertGreater(result.wage, cap)
        self.assertLessEqual(expected, 100.0 + (cap - reservation) * HOURS + 1e-6)
        self.assertGreater(expected, 100.0)

    def test_the_heading_wage_is_capped_in_the_clearing_itself(self):
        held = state(healers=1.0)
        year_inputs = inputs([hungry()])
        cap = long_run_cap(held, year_inputs)
        result = settle(held, year_inputs)
        self.assertLessEqual(result.heading_wage, cap + 1e-9)


class CeilingFunction(unittest.TestCase):

    def test_the_worth_is_hours_weighted_and_not_under_the_reservation(self):
        bids = [Bid("a", "healer", "vale", 90.0, 4.0), Bid("b", "healer", "vale", 10.0, 14.0), Bid("c", "healer", "vale", 5.0, 0.5)]
        self.assertAlmostEqual(scarcity.bid_weighted_worth(bids, 1.0), (90 * 4.0 + 10 * 14.0) / 100.0)
        self.assertEqual(scarcity.bid_weighted_worth([], 1.0), 1.0)

    def test_an_import_cost_below_the_worth_binds(self):
        self.assertEqual(scarcity.short_run_ceiling(2.0, 1.0, 5.0, [hungry(maximum=9.0)], 3.0), 3.0)
        self.assertEqual(scarcity.short_run_ceiling(2.0, 1.0, 5.0, [hungry(maximum=9.0)], None), 9.0)


if __name__ == "__main__":
    unittest.main()
