"""Migration over the tables (`migration_kernel`) gives what the plain rule on dicts gave (kept in `labour_migration_plain`): the
same workers and the same net change per area, in the same order, bit for bit, on random states, routes and clearings."""

QUICK_TOPIC = True

import random
import unittest

from sim.labour.market import aptitude, migration, trades
from sim.labour.market.records import MarketState, Route, YearInputs, YearReport
from sim.tests import labour_migration_plain as plain
from sim.tests.test_labour_switching_tables import REGISTRY, TRADES, random_clearing


def random_case(rng):
    bands = aptitude.band_count()
    areas = ["a%d" % each for each in range(rng.randint(2, 5))]
    workers = {area: {trade: [rng.uniform(0, 400) * rng.choice([0, 1, 1]) for _ in range(bands)] for trade in rng.sample(TRADES, rng.randint(0, len(TRADES)))}
               for area in areas if rng.random() < 0.9}
    clearings = {(area, trade): random_clearing(rng, area, trade) for area in areas for trade in TRADES if rng.random() < 0.7}
    routes = {area: [Route(rng.choice(areas), rng.uniform(0, 5000), rng.choice([0.0, rng.uniform(0, 3000)])) for _ in range(rng.randint(0, 4))]
              for area in areas if rng.random() < 0.9}
    inputs = YearInputs(trades=trades.trade_specs(REGISTRY), bids=[], subsistence_per_worker_year={area: rng.uniform(5000, 30000) for area in areas if rng.random() < 0.9},
                        hours_per_worker_year=2000.0, discount_rate=0.05, career_years=30.0, routes=routes,
                        taxed_share={area: rng.uniform(0, 0.6) for area in areas if rng.random() < 0.5})
    return MarketState(workers=workers), inputs, clearings


class MigrationOverTablesIsTheDictRule(unittest.TestCase):
    def test_random_years(self):
        rng = random.Random(12)
        moved = 0
        for _case in range(120):
            state, inputs, clearings = random_case(rng)
            other = state.copy()
            want_report, got_report = YearReport(), YearReport()
            plain.migrate(other, inputs, clearings, want_report)
            migration.migrate(state, inputs, clearings, got_report)
            self.assertEqual(state.to_plain(), other.to_plain())
            self.assertEqual(list(got_report.migrated.items()), list(want_report.migrated.items()), "net change per area, in order")
            self.assertEqual(list(state.workers), list(other.workers))
            for area in other.workers:
                self.assertEqual(list(state.workers[area]), list(other.workers[area]))
            moved += bool(want_report.migrated)
        self.assertGreater(moved, 20, "the random cases should move people")


if __name__ == "__main__":
    unittest.main()
