"""Whole years of the labour core on invented trades and places: demand pulls people into a trade, a
hard trade keeps a premium an easy one with the same training loses, an employer paying over the market
staffs first, a school seeds a trade nobody practised, workers follow pay between places, and nobody is
created or lost on the way."""
import time
import unittest

from sim.labour.market import aptitude, records, trades, year

REGISTRY = {
    "digger": {"family": "toil", "training_years": 0},
    "carver": {"family": "craft", "training_years": 3},
    "joiner": {"family": "craft", "training_years": 3},
    "healer": {"family": "lore", "training_years": 3, "difficulty": 1.2},
    "plainhand": {"family": "lore", "training_years": 3, "difficulty": -1.5},
}
HOURS = 2000.0


def bid(employer, trade, area, workers, maximum_wage=5.0, premium=0.0):
    return records.Bid(employer=employer, trade=trade, area=area, hours=workers * HOURS,
                       maximum_wage=maximum_wage, pay_premium=premium)


def inputs(bids, areas=("vale",), entrants=0.0, attrition=0.0, routes=None, schools=()):
    return records.YearInputs(
        trades=trades.trade_specs(REGISTRY), bids=bids,
        subsistence_per_worker_year={area: HOURS for area in areas}, hours_per_worker_year=HOURS,
        discount_rate=0.05, career_years=30.0,
        entrants={area: entrants for area in areas}, attrition_share={area: attrition for area in areas},
        routes=routes or {}, schools=schools)


def town(**people_by_trade):
    return {trade: aptitude.split_evenly(count) for trade, count in people_by_trade.items()}


def run(state, year_inputs, years):
    report = None
    for _year in range(years):
        state, report = year.run_year(state, year_inputs)
    return state, report


def workers(state, area, trade):
    return aptitude.band_total(state.workers.get(area, {}).get(trade, aptitude.empty_bands()))


class ConservationTests(unittest.TestCase):
    def test_people_are_neither_created_nor_lost(self):
        state = records.MarketState(workers={"vale": town(digger=1000, carver=50),
                                             "port": town(digger=500, joiner=40)})
        routes = {"vale": [records.Route("port", 100.0)], "port": [records.Route("vale", 100.0)]}
        year_inputs = inputs([bid("yard", "joiner", "port", 200, maximum_wage=8.0),
                              bid("farm", "digger", "vale", 900)], areas=("vale", "port"), routes=routes)
        before = records.people_in(state)
        state, _report = run(state, year_inputs, 10)
        self.assertAlmostEqual(records.people_in(state), before, places=6)

    def test_entrants_and_attrition_are_the_only_doors(self):
        state = records.MarketState(workers={"vale": town(digger=1000, carver=100)})
        year_inputs = inputs([bid("farm", "digger", "vale", 900)], entrants=30.0, attrition=0.02)
        before = records.people_in(state)
        state, report = year.run_year(state, year_inputs)
        self.assertAlmostEqual(records.people_in(state), before + 30.0 - report.left_work["vale"], places=6)

    def test_the_given_state_is_not_changed(self):
        state = records.MarketState(workers={"vale": town(digger=100)})
        year.run_year(state, inputs([bid("farm", "digger", "vale", 50)], entrants=10.0))
        self.assertEqual(workers(state, "vale", "digger"), 100.0)


class DemandTests(unittest.TestCase):
    def test_demand_raises_the_wage_and_pulls_people_in(self):
        state = records.MarketState(workers={"vale": town(digger=1000, carver=20)})
        year_inputs = inputs([bid("farm", "digger", "vale", 1000), bid("yard", "carver", "vale", 120)],
                             entrants=25.0, attrition=0.02)
        state, report = run(state, year_inputs, 3)
        early_wage = report.clearing("carver", "vale").wage
        self.assertGreater(early_wage, report.clearing("digger", "vale").wage)
        state, report = run(state, year_inputs, 45)
        self.assertGreater(workers(state, "vale", "carver"), 60.0)
        self.assertLess(report.clearing("carver", "vale").wage, early_wage)


class AptitudeTests(unittest.TestCase):
    def test_a_hard_trade_keeps_a_premium_an_easy_one_with_equal_training_loses(self):
        state = records.MarketState(workers={"vale": town(digger=2000, healer=30, plainhand=30)})
        year_inputs = inputs([bid("farm", "digger", "vale", 2000), bid("temple", "healer", "vale", 100, 20.0),
                              bid("office", "plainhand", "vale", 100, 20.0)], entrants=60.0, attrition=0.025)
        state, _report = run(state, year_inputs, 60)
        healer_wages, plainhand_wages = [], []
        for _year in range(60):   # vertical demand cycles, so compare the averages over a long stretch
            state, report = year.run_year(state, year_inputs)
            healer_wages.append(report.clearing("healer", "vale").wage)
            plainhand_wages.append(report.clearing("plainhand", "vale").wage)
        self.assertGreater(sum(healer_wages), 1.2 * sum(plainhand_wages))
        healers = state.workers["vale"]["healer"]
        self.assertGreater(healers[-1], healers[0])


class PayOverTheMarketTests(unittest.TestCase):
    def test_the_employer_paying_more_is_staffed_first(self):
        state = records.MarketState(workers={"vale": town(digger=500, carver=60)})
        year_inputs = inputs([bid("farm", "digger", "vale", 500), bid("mean", "carver", "vale", 60),
                              bid("generous", "carver", "vale", 60, maximum_wage=10.0, premium=0.3)])
        state, report = run(state, year_inputs, 3)
        hired = report.clearing("carver", "vale").hired_by_employer
        self.assertGreater(hired.get("generous", 0.0), hired.get("mean", 0.0))


class SchoolTests(unittest.TestCase):
    def test_a_school_seeds_a_trade_nobody_practised(self):
        state = records.MarketState(workers={"vale": town(digger=1000)})
        bids = [bid("farm", "digger", "vale", 1000), bid("yard", "joiner", "vale", 40, 10.0)]
        without, _report = run(state, inputs(bids, entrants=20.0), 6)
        self.assertEqual(workers(without, "vale", "joiner"), 0.0)
        school = records.School(owner="founder", trade="joiner", area="vale", seats=20.0)
        taught, _report = run(state, inputs(bids, entrants=20.0, schools=[school]), 6)
        self.assertGreater(workers(taught, "vale", "joiner"), 5.0)


class MigrationTests(unittest.TestCase):
    def test_workers_follow_pay_to_another_place(self):
        state = records.MarketState(workers={"vale": town(carver=100, digger=100), "port": town(carver=100, digger=100)})
        routes = {"vale": [records.Route("port", 500.0)], "port": [records.Route("vale", 500.0)]}
        year_inputs = inputs([bid("yard", "carver", "port", 180, 10.0), bid("yard", "carver", "vale", 40, 10.0),
                              bid("farm", "digger", "vale", 100), bid("farm", "digger", "port", 100)],
                             areas=("vale", "port"), routes=routes)
        state, _report = run(state, year_inputs, 10)
        self.assertGreater(workers(state, "port", "carver"), workers(state, "vale", "carver"))


class SteadinessTests(unittest.TestCase):
    """With demand that falls with the wage, a trained trade settles above the floor and stays there:
    entrants weigh those already in training, and nobody switches into a trade that pays no more."""

    def test_a_trained_trade_settles_at_a_premium_without_cycling(self):
        state = records.MarketState(workers={"vale": town(digger=2400, carver=30, joiner=30)})
        sloped = [bid("employer%d" % tranche, trade, "vale", workers / 5.0, 3.0 * (1.3 - 0.3 * tranche))
                  for tranche in range(5) for trade, workers in (("carver", 30), ("joiner", 30), ("digger", 2000))]
        year_inputs = inputs(sloped, entrants=85.0, attrition=1 / 30.0)
        state, _report = run(state, year_inputs, 80)
        wages = []
        for _year in range(40):
            state, report = year.run_year(state, year_inputs)
            wages.append(report.clearing("carver", "vale").wage)
        floor = 1.0
        self.assertGreater(min(wages), floor)
        self.assertLess(max(wages) - min(wages), 0.5 * (sum(wages) / len(wages) - floor) + 0.2)

    def test_nobody_drifts_into_a_glutted_trade(self):
        state = records.MarketState(workers={"vale": town(digger=1000, carver=60)})
        year_inputs = inputs([bid("farm", "digger", "vale", 400, 0.9), bid("yard", "carver", "vale", 20, 0.9)])
        _state, report = year.run_year(state, year_inputs)
        self.assertLessEqual(report.switched.get("vale", {}).get("carver", 0.0), 0.0)


class SpeedTests(unittest.TestCase):
    def test_a_year_over_many_places_stays_cheap(self):
        areas = ["area%d" % index for index in range(100)]
        state = records.MarketState(workers={area: town(digger=1000, carver=50, joiner=50, healer=10, plainhand=20)
                                             for area in areas})
        routes = {area: [records.Route(areas[(index + 1) % len(areas)], 100.0),
                         records.Route(areas[index - 1], 100.0)] for index, area in enumerate(areas)}
        bids = [bid("employer", trade, area, 30 + index % 7, 6.0)
                for index, area in enumerate(areas) for trade in REGISTRY]
        year_inputs = inputs(bids, areas=areas, entrants=20.0, attrition=0.02, routes=routes)
        started = time.process_time()
        year.run_year(state, year_inputs)
        self.assertLess(time.process_time() - started, 2.0)


if __name__ == "__main__":
    unittest.main()
