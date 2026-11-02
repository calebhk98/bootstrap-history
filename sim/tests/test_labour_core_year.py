"""Whole years of the labour core on invented trades and places: an employer paying over the market staffs first,
workers follow pay between places, a trade nobody wants to switch into is not drifted into, and nobody is created or
lost on the way."""

QUICK_TOPIC = True

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


def bid(employer, trade, area, workers, maximum_wage=5.0):
    return records.Bid(employer=employer, trade=trade, area=area, hours=workers * HOURS,
                       maximum_wage=maximum_wage)


def inputs(bids, areas=("vale",), routes=None, schools=()):
    return records.YearInputs(
        trades=trades.trade_specs(REGISTRY), bids=bids,
        subsistence_per_worker_year={area: HOURS for area in areas}, hours_per_worker_year=HOURS,
        discount_rate=0.05, career_years=30.0,
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

    def test_the_given_state_is_not_changed(self):
        state = records.MarketState(workers={"vale": town(digger=100)})
        year.run_year(state, inputs([bid("farm", "digger", "vale", 50)]))
        self.assertEqual(workers(state, "vale", "digger"), 100.0)


class HigherMaximumTests(unittest.TestCase):
    def test_the_employer_valuing_hours_more_is_staffed_first(self):
        state = records.MarketState(workers={"vale": town(digger=500, carver=60)})
        year_inputs = inputs([bid("farm", "digger", "vale", 500), bid("mean", "carver", "vale", 60),
                              bid("generous", "carver", "vale", 60, maximum_wage=10.0)])
        state, report = run(state, year_inputs, 3)
        hired = report.clearing("carver", "vale").hired_by_employer
        self.assertGreater(hired.get("generous", 0.0), hired.get("mean", 0.0))


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
    switchers weigh those already in training, and nobody switches into a trade that pays no more."""

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
        year_inputs = inputs(bids, areas=areas, routes=routes)
        started = time.process_time()
        year.run_year(state, year_inputs)
        self.assertLess(time.process_time() - started, 2.0)


if __name__ == "__main__":
    unittest.main()
