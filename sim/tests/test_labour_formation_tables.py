"""Formation of empty trades over the tables (`formation_year.form_all`) gives what the plain rule on dicts gave (kept in
`labour_formation_plain`): the same people moved, the same bonded lots bought and paid for, in the same order, bit for bit, on random
states, routes, bids and clearings."""

QUICK_TOPIC = True

import random
import unittest

from sim.labour.market import aptitude, formation, trades
from sim.labour.market.records import EmployerHoursBid, LabourClearing, MarketState, Route, YearInputs, YearReport
from sim.tests import labour_formation_plain as plain

REGISTRY = {"digger": {"family": "toil", "training_years": 0}, "carver": {"family": "craft", "training_years": 3},
            "healer": {"family": "lore", "training_years": 6, "difficulty": 1.0}}
TRADES = sorted(REGISTRY)
EMPLOYERS = ["forge", "mill", "yard", "quarry"]


def random_clearing(rng, area, trade):
    wanted = rng.choice([0.0, rng.uniform(500, 9000)])
    hired = rng.choice([0.0, rng.uniform(0, wanted)]) if wanted > 0 else 0.0
    by_employer = {employer: rng.uniform(1, hired + 1.0) for employer in rng.sample(EMPLOYERS, rng.randint(0, 3))} if hired > 0 else {}
    return LabourClearing(trade=trade, area=area, wage=rng.uniform(0.4, 5.0), hours_offered=rng.uniform(0, 5000), hours_wanted=wanted,
                          hours_hired=hired, hired_by_employer=by_employer, target_wage=rng.choice([None, rng.uniform(0.4, 6.0)]))


def random_case(rng):
    bands = aptitude.band_count()
    areas = ["a%d" % each for each in range(rng.randint(2, 5))]
    workers = {area: {trade: [rng.uniform(0, 300) * rng.choice([0, 1, 1]) for _ in range(bands)] for trade in rng.sample(TRADES, rng.randint(0, len(TRADES)))}
               for area in areas if rng.random() < 0.8}
    trainees = {area: {trade: [[2.0, [rng.uniform(0, 5) for _ in range(bands)], 0.0]] for trade in rng.sample(TRADES, rng.randint(0, 2))}
                for area in areas if rng.random() < 0.3}
    clearings = {(area, trade): random_clearing(rng, area, trade) for area in areas for trade in TRADES if rng.random() < 0.8}
    routes = {area: [Route(rng.choice(areas), rng.uniform(0, 5000)) for _ in range(rng.randint(0, 3))] for area in areas if rng.random() < 0.9}
    bids = [EmployerHoursBid(rng.choice(EMPLOYERS), trade, area, rng.uniform(0, 5000), rng.uniform(0.5, 6.0))
            for area in areas for trade in TRADES for _ in range(rng.randint(0, 3))]
    inputs = YearInputs(trades=trades.trade_specs(REGISTRY), bids=bids, subsistence_per_worker_year={area: rng.uniform(5000, 30000) for area in areas},
                        hours_per_worker_year=2000.0, discount_rate=0.05, career_years=30.0, routes=routes,
                        ask_floor_per_worker_year={area: rng.uniform(3000, 20000) for area in areas if rng.random() < 0.8},
                        bondage_allowed=frozenset(area for area in areas if rng.random() < 0.7),
                        bonded_for_sale={area: {trade: rng.choice([0.0, rng.uniform(0, 40)]) for trade in TRADES if rng.random() < 0.8}
                                         for area in areas if rng.random() < 0.8},
                        outlay_room={employer: rng.choice([0.0, rng.uniform(0, 3e8)]) for employer in EMPLOYERS if rng.random() < 0.8})
    return MarketState(workers=workers, trainees=trainees), inputs, clearings


class FormationOverTablesIsTheDictRule(unittest.TestCase):
    def test_random_years(self):
        rng = random.Random(21)
        migrated = bought = 0
        for _case in range(150):
            state, inputs, clearings = random_case(rng)
            other = state.copy()
            want_report, got_report = YearReport(), YearReport()
            plain.form_trades(other, inputs, clearings, want_report)
            formation.form_trades(state, inputs, clearings, got_report)
            self.assertEqual(state.to_plain(), other.to_plain())
            self.assertEqual([(area, [(trade, list(routes.items())) for trade, routes in by_trade.items()]) for area, by_trade in got_report.formed.items()],
                             [(area, [(trade, list(routes.items())) for trade, routes in by_trade.items()]) for area, by_trade in want_report.formed.items()],
                             "what was formed, by route, in order")
            self.assertEqual(got_report.bonded_lots, want_report.bonded_lots)
            self.assertEqual(list(state.workers), list(other.workers))
            for area in other.workers:
                self.assertEqual(list(state.workers[area]), list(other.workers[area]))
            migrated += any("migration" in routes for by_trade in want_report.formed.values() for routes in by_trade.values())
            bought += bool(want_report.bonded_lots)
        self.assertGreater(migrated, 5, "the random cases should send migrants")
        self.assertGreater(bought, 10, "the random cases should buy bonded people")


if __name__ == "__main__":
    unittest.main()
