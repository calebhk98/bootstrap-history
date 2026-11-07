"""Numba port, labour switching: the moves an area plans in a round (`switching._planned_moves`, over arrays by
`switching_kernel.plan_area`) agree with the plain Python rules kept in `labour_switching_reference`, over several
rounds in which destinations' incomes after training move by less and by more than the plan-reuse tolerance; no game.

The kernel sums the logit weights left to right where the plain code used `math.fsum`, so amounts agree to a relative
tolerance."""

QUICK_TOPIC = True

import random
import unittest

import numpy as np

from sim.labour.market import aptitude, switching
from sim.labour.market.records import MarketState, TradeSpec, YearInputs
from sim.tests import labour_switching_reference as reference

TOLERANCE = 1e-12


def random_inputs(rng, count_trades):
    specs = {}
    for index in range(count_trades):
        specs["t%02d" % index] = TradeSpec("t%02d" % index, rng.choice(["earth", "metal", "mind"]), rng.choice([0.0, 1.0, 3.0, 7.0]),
                                           rng.uniform(-1.0, 2.0), 0.0, index == 0)
    return YearInputs(trades=specs, bids=(), subsistence_per_worker_year={"vale": 300.0}, hours_per_worker_year=300.0,
                      discount_rate=rng.choice([0.0, 0.03, 0.06]), career_years=rng.choice([0.0, 30.0, 40.0]))


def moves_equal(test, got, expected):
    """The moves in the order `_carry_out` takes them (by destination, source, training share); the order a source lists its
    destinations in does not matter."""
    got, expected = (sorted(each, key=switching._move_order) for each in (got, expected))
    test.assertEqual([(move[0], move[1], move[3]) for move in got], [(move[0], move[1], move[3]) for move in expected])
    for left, right in zip(got, expected):
        for amount, wanted in zip(left[2], right[2]):
            test.assertAlmostEqual(amount, wanted, delta=TOLERANCE * max(1.0, abs(wanted)))


class PlannedMovesAgreeWithThePlainRules(unittest.TestCase):

    def test_four_rounds_of_random_areas(self):
        rng = random.Random(21)
        rounds_compared = rounds_moving = 0
        for _case in range(60):
            inputs = random_inputs(rng, rng.randint(2, 9))
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
            fixed = switching._DestinationArrays(
                chances=np.array([chances[trade] for trade in destinations]), years=np.array([inputs.trades[trade].training_years for trade in destinations]),
                families=[inputs.trades[trade].family for trade in destinations],
                position={trade: position for position, trade in enumerate(destinations)}, fallback_position=0)
            plan = switching._AreaPlan(inputs, fixed, sources, fallback, income, idle, baseline, vacancies, destinations, subsistence)
            for _round in range(4):
                expected = reference._planned_moves(state, inputs, "vale", sources, destinations, income, baseline, later, vacancies,
                                                    subsistence, chances, planned, idle)
                got = switching._planned_moves(inputs, state.workers["vale"], plan, np.array([later[trade] for trade in destinations]))
                moves_equal(self, got, expected)
                rounds_compared += 1
                rounds_moving += bool(expected)
                for trade in destinations:      # enrolling moves some incomes a little, some a lot
                    later[trade] += rng.choice([0.0, 0.004 * subsistence, rng.uniform(-200.0, 200.0)])
                for move in expected[:2]:       # and the sources that sent people hold fewer
                    bands = state.workers["vale"][move[0]]
                    for band, amount in enumerate(move[2]):
                        bands[band] = max(0.0, bands[band] - amount)
        self.assertGreater(rounds_compared, 200)
        self.assertGreater(rounds_moving, 100)


if __name__ == "__main__":
    unittest.main()
