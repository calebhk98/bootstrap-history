"""Migration in the labour-market core, on hand-built records."""
import random
import unittest

from sim.labour.market.migration import migrate
from sim.labour.market.records import Clearing, MarketState, Route, YearInputs, YearReport

BANDS = 5


def everyone(state):
    """People in workers and trainee cohorts ([years_left, bands, bonus])."""
    total = 0.0
    for trades in state.workers.values():
        for bands in trades.values():
            total += sum(bands)
    for trades in state.trainees.values():
        for cohorts in trades.values():
            for cohort in cohorts:
                total += sum(cohort[1])
    return total


def clearing(area, trade, wage):
    hours = 1000.0
    return Clearing(trade=trade, area=area, wage=wage, hours_offered=hours, hours_wanted=hours,
                    hours_hired=hours, hired_by_employer={}, paid_by_employer={}, average_wage=wage)


def world(vale_wage=1.0, port_wage=2.0, cost=0.0, trainees=False):
    state = MarketState(workers={"vale": {"digger": [100.0] * BANDS}, "port": {"digger": [100.0] * BANDS}})
    if trainees:
        state.trainees = {"vale": {"digger": [[2.0, [10.0] * BANDS, 0.0]]}}
    inputs = YearInputs(trades={}, bids=[], subsistence_per_worker_year={"vale": 100.0, "port": 100.0},
                        hours_per_worker_year=100.0, discount_rate=0.05, career_years=30.0,
                        routes={"vale": [Route("port", cost)], "port": [Route("vale", cost)]})
    clearings = {("vale", "digger"): clearing("vale", "digger", vale_wage),
                 ("port", "digger"): clearing("port", "digger", port_wage)}
    return state, inputs, clearings


def add_hill(state, inputs, clearings):
    inputs.subsistence_per_worker_year["hill"] = 50.0
    inputs.routes["vale"].append(Route("hill", 5.0))
    inputs.routes["hill"] = [Route("vale", 5.0), Route("port", 7.0)]
    state.workers["hill"] = {"digger": [40.0] * BANDS}
    clearings[("hill", "digger")] = clearing("hill", "digger", 1.5)


def run(state, inputs, clearings):
    report = YearReport()
    migrate(state, inputs, clearings, report)
    return report


class MigrationTests(unittest.TestCase):
    def test_workers_move_toward_the_higher_real_wage(self):
        state, inputs, clearings = world()
        report = run(state, inputs, clearings)
        self.assertGreater(report.migrated["port"], 0.0)
        self.assertLess(report.migrated["vale"], 0.0)
        self.assertLess(sum(state.workers["vale"]["digger"]), 500.0)

    def test_a_dearer_move_sends_fewer(self):
        movers = []
        for cost in (0.0, 50.0, 300.0):
            state, inputs, clearings = world(cost=cost)
            movers.append(run(state, inputs, clearings).migrated["port"])
        self.assertGreater(movers[0], movers[1])
        self.assertGreater(movers[1], movers[2])

    def test_no_routes_nobody_moves(self):
        state, inputs, clearings = world()
        inputs.routes = {}
        report = run(state, inputs, clearings)
        self.assertEqual(report.migrated, {})
        self.assertEqual(state.workers["vale"]["digger"], [100.0] * BANDS)

    def test_equal_wages_move_almost_nobody(self):
        state, inputs, clearings = world(vale_wage=2.0, port_wage=2.0, cost=20.0)
        report = run(state, inputs, clearings)
        self.assertLess(abs(report.migrated["port"]), 0.02 * 500.0)

    def test_people_are_conserved(self):
        state, inputs, clearings = world(cost=10.0, trainees=True)
        add_hill(state, inputs, clearings)
        before = everyone(state)
        report = run(state, inputs, clearings)
        self.assertAlmostEqual(everyone(state), before, places=9)
        self.assertAlmostEqual(sum(report.migrated.values()), 0.0, places=9)
        for trades in state.workers.values():
            self.assertTrue(all(count >= 0.0 for count in trades["digger"]))

    def test_order_does_not_matter(self):
        results = []
        for seed in range(4):
            state, inputs, clearings = world(cost=10.0)
            add_hill(state, inputs, clearings)
            rng = random.Random(seed)
            for routes in inputs.routes.values():
                rng.shuffle(routes)
            areas = list(inputs.routes)
            rng.shuffle(areas)
            inputs.routes = {area: inputs.routes[area] for area in areas}
            run(state, inputs, clearings)
            results.append({area: state.workers[area]["digger"] for area in sorted(state.workers)})
        for other in results[1:]:
            self.assertEqual(other, results[0])

    def test_trainees_stay(self):
        state, inputs, clearings = world(trainees=True)
        run(state, inputs, clearings)
        self.assertEqual(state.trainees["vale"]["digger"], [[2.0, [10.0] * BANDS, 0.0]])
        self.assertNotIn("port", state.trainees)


if __name__ == "__main__":
    unittest.main()
