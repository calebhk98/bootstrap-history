"""Numba port, labour switching: the moves an area plans in a round (`switching._planned_moves`, over arrays by
`switching_kernel.plan_area`) agree with the plain Python rules kept in `labour_switching_reference`, over several
rounds in which destinations' incomes after training move by less and by more than the plan-reuse tolerance; no game.

The kernel sums the logit weights left to right where the plain code used `math.fsum`, so amounts agree to a relative
tolerance."""

QUICK_TOPIC = True

import random
import unittest

import numpy as np

from sim.labour.market import aptitude
from sim.tests import labour_switching_plain as switching
from sim.labour.market.records import MarketState, School, TradeSpec, YearInputs, YearReport, copy_state
from sim.tests import labour_switching_reference as reference

TOLERANCE = 1e-12


def random_inputs(rng, count_trades, schools=False):
    specs = {}
    for index in range(count_trades):
        specs["t%02d" % index] = TradeSpec("t%02d" % index, rng.choice(["earth", "metal", "mind"]), rng.choice([0.0, 1.0, 3.0, 7.0]),
                                           rng.uniform(-1.0, 2.0), 0.0, index == 0)
    seats = [School("crown", trade, "vale", rng.uniform(1.0, 200.0), rng.choice([0.0, 0.3])) for trade in specs if schools and rng.random() < 0.5]
    return YearInputs(trades=specs, bids=(), subsistence_per_worker_year={"vale": 300.0}, hours_per_worker_year=300.0,
                      discount_rate=rng.choice([0.0, 0.03, 0.06]), career_years=rng.choice([0.0, 30.0, 40.0]), schools=seats)


def moves_equal(test, got, expected):
    """The moves in the order `_carry_out` takes them (by destination, source, training share); the order a source lists its
    destinations in does not matter."""
    got, expected = (sorted(each, key=switching._move_order) for each in (got, expected))
    test.assertEqual([(move[0], move[1], move[3]) for move in got], [(move[0], move[1], move[3]) for move in expected])
    for left, right in zip(got, expected):
        for amount, wanted in zip(left[2], right[2]):
            test.assertAlmostEqual(amount, wanted, delta=TOLERANCE * max(1.0, abs(wanted)))


def merged(cohorts):
    """The cohorts with neighbours of one finish date and one teaching joined: a teaching bonus that differs in its last digit
    (the places it is a share of are summed in another order) is the same teaching."""
    joined = []
    for years, bands, bonus in cohorts:
        if sum(bands) < 1e-9:      # a cohort the places filled to the last digit admits nobody on one side and a rounding error on the other
            continue
        if joined and joined[-1][0] == years and abs(joined[-1][2] - bonus) <= 1e-12:
            joined[-1] = [years, [one + two for one, two in zip(joined[-1][1], bands)], joined[-1][2]]
        else:
            joined.append([years, list(bands), bonus])
    return joined


class PlannedMovesAgreeWithThePlainRules(unittest.TestCase):

    def assert_states_close(self, left, right):
        self.assertEqual({a: sorted(by) for a, by in left.workers.items()}, {a: sorted(by) for a, by in right.workers.items()})
        for area, by_trade in left.workers.items():
            for trade, bands in by_trade.items():
                for one, other in zip(bands, right.workers[area][trade]):
                    self.assertAlmostEqual(one, other, delta=1e-9 * max(1.0, abs(one)))
        self.assertEqual({a: sorted(by) for a, by in left.trainees.items()}, {a: sorted(by) for a, by in right.trainees.items()})
        for area, by_trade in left.trainees.items():
            for trade, cohorts in by_trade.items():
                one_side, other_side = merged(cohorts), merged(right.trainees[area][trade])
                self.assertEqual(len(one_side), len(other_side), (trade, one_side, other_side))
                for cohort, other in zip(one_side, other_side):
                    self.assertEqual(cohort[0], other[0])
                    self.assertAlmostEqual(cohort[2], other[2], delta=1e-12)      # the seats' share of the places sums in another order
                    for one, two in zip(cohort[1], other[1]):
                        self.assertAlmostEqual(one, two, delta=1e-9 * max(1.0, abs(one)))

    def test_four_rounds_of_random_areas(self):
        self.compare_rounds(21, False)

    def test_four_rounds_of_random_areas_with_schools(self):
        self.compare_rounds(22, True)

    def compare_rounds(self, seed, schools):
        rng = random.Random(seed)
        rounds_compared = rounds_moving = 0
        for _case in range(60):
            inputs = random_inputs(rng, rng.randint(2, 9), schools)
            destinations = sorted(inputs.trades)
            fallback = destinations[0]
            sources = [trade for trade in destinations if rng.random() < 0.7] or [fallback]
            state = MarketState(workers={"vale": {trade: [rng.choice([0.0, rng.uniform(0.0, 500.0)]) for _band in range(aptitude.band_count())]
                                                  for trade in sources}})
            subsistence = 300.0
            chances = {trade: aptitude.completion_by_band(inputs.trades[trade].difficulty) for trade in destinations}
            income = {trade: rng.uniform(150.0, 900.0) for trade in sources}
            idle = {trade: rng.choice([0.0, rng.random()]) for trade in sources}
            baseline = rng.uniform(150.0, 500.0)
            vacancies = {trade for trade in destinations if rng.random() < 0.3}
            later = {trade: rng.uniform(150.0, 1200.0) for trade in destinations}
            planned = {}
            state_fast = copy_state(state)
            fixed = switching._DestinationArrays(
                chances=np.array([chances[trade] for trade in destinations]), years=np.array([inputs.trades[trade].training_years for trade in destinations]),
                families=[inputs.trades[trade].family for trade in destinations],
                position={trade: position for position, trade in enumerate(destinations)}, fallback_position=0)
            plan = switching._AreaPlan(inputs, fixed, sources, fallback, income, idle, baseline, vacancies, destinations, subsistence)
            for _round in range(4):
                expected = reference._planned_moves(state, inputs, "vale", sources, destinations, income, baseline, later, vacancies,
                                                    subsistence, chances, planned, idle)
                found = switching._planned_moves(inputs, state_fast.workers["vale"], plan, np.array([later[trade] for trade in destinations]))
                got = [] if found is None else found.as_tuples(plan)
                moves_equal(self, got, expected)
                rounds_compared += 1
                rounds_moving += bool(expected)
                # both ways of carrying the moves out leave the same people in training and at work
                report_plain, report_fast = YearReport(), YearReport()
                targets_plain = reference._carry_out(state, inputs, report_plain, "vale", expected)
                targets_fast = switching._carry_out(state_fast, inputs, report_fast, "vale", plan, found)
                self.assertEqual(targets_plain, targets_fast)
                self.assert_states_close(state, state_fast)
                self.assertEqual(sorted(report_plain.switched.get("vale", {})), sorted(report_fast.switched.get("vale", {})))
                for trade, change in report_plain.switched.get("vale", {}).items():
                    self.assertAlmostEqual(report_fast.switched["vale"][trade], change, delta=1e-9 * max(1.0, abs(change)))
                for trade in destinations:      # enrolling moves some incomes a little, some a lot
                    later[trade] += rng.choice([0.0, 0.004 * subsistence, rng.uniform(-200.0, 200.0)])
        self.assertGreater(rounds_compared, 200)
        self.assertGreater(rounds_moving, 100)


if __name__ == "__main__":
    unittest.main()
