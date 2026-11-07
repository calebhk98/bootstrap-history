"""Complaint 497: the labour year's remaining reads and sums give the answers of the ones they replaced. Each is called
beside a copy of the old one on random inputs; no game."""

QUICK_TOPIC = True

import math
import random
import unittest

from sim.economy import kept_wages, market_memory, priced_reads
from sim.labour.market import expectations, migration
from sim.labour.market.carriage import carriage_from
from sim.labour.market.records import MarketState, Route, YearInputs


def old_move_shares(real_origin, options):
    """The migration rule as it was: the stay option and each weighable route a score, shared out by `logit_shares`."""
    scores = {"stay": 0.0}
    for position, (real_destination, cost_in_years) in enumerate(options):
        if real_destination is None or real_destination <= 0.0:
            continue
        scores[str(position)] = math.log(real_destination) - math.log(real_origin) - migration.MIGRATION_COST_WEIGHT * cost_in_years
    if len(scores) == 1:
        return [0.0] * len(options)
    shares = expectations.logit_shares(scores, migration.MIGRATION_TASTE_SCALE)
    return [shares.get(str(position), 0.0) * migration.MIGRATION_CONSIDERATION_SHARE_PER_YEAR for position in range(len(options))]


def old_graduates_coming(state, area, trade, completion_by_band):
    total = 0.0
    for cohort in state.trainees.get(area, {}).get(trade, []):
        total += math.fsum(count * chance for count, chance in zip(cohort[1], completion_by_band))
    return total


class MigrationSharesAgreeWithTheLogit(unittest.TestCase):

    def test_random_options(self):
        rng = random.Random(5)
        for _case in range(300):
            options = [(rng.choice([None, 0.0, -1.0, rng.uniform(0.2, 5.0)]), rng.uniform(0.0, 3.0)) for _option in range(rng.randint(0, 7))]
            origin = rng.uniform(0.2, 5.0)
            got, want = migration.move_shares(origin, options), old_move_shares(origin, options)
            self.assertEqual(len(got), len(want))
            for left, right in zip(got, want):
                # the stay weight joins the sum in a different place than the dictionary's, so the last digits differ
                self.assertAlmostEqual(left, right, delta=1e-12 * max(1.0, abs(right)))


class GraduatesComingAgreeWithTheOldSum(unittest.TestCase):

    def test_random_trainees(self):
        rng = random.Random(9)
        for _case in range(100):
            bands = rng.randint(1, 5)
            chances = tuple(rng.uniform(0.0, 1.0) for _band in range(bands))
            cohorts = [[rng.uniform(0.0, 5.0), [rng.uniform(0.0, 40.0) for _band in range(bands)], 0.0] for _cohort in range(rng.randint(0, 4))]
            state = MarketState(trainees={"a": {"t": cohorts}} if rng.random() < 0.9 else {})
            got = expectations.graduates_coming(state, "a", "t", chances)
            want = old_graduates_coming(state, "a", "t", chances)
            self.assertAlmostEqual(got, want, delta=1e-12 * max(1.0, want))


class CarriageIsSearchedOncePerOrigin(unittest.TestCase):

    def test_the_year_inputs_answer_the_search_and_share_it(self):
        rng = random.Random(3)
        areas = ["a%d" % i for i in range(8)]
        routes = {area: [Route(other, rng.uniform(-5, 80)) for other in areas if rng.random() < 0.3] for area in areas}
        inputs = YearInputs(trades={}, bids=[], subsistence_per_worker_year={}, hours_per_worker_year=2000.0,
                            discount_rate=0.05, career_years=40.0, routes=routes)
        for origin in areas:
            self.assertEqual(inputs.carriage_from(origin), carriage_from(routes, origin))
            self.assertIs(inputs.carriage_from(origin), inputs.carriage_from(origin))


class KeptReadsHoldUntilTheMemoryIsWritten(unittest.TestCase):

    def test_a_view_read_is_computed_once_until_a_write(self):
        class View:
            def __init__(self):
                self.reads = {}

            def _current(self):
                return self.reads

        view, calls = View(), []
        compute = lambda: calls.append(1) or len(calls)
        self.assertEqual(priced_reads.kept_reads(view, "k", compute), 1)
        self.assertEqual(priced_reads.kept_reads(view, "k", compute), 1)
        view.reads = {}      # what a write to the memory does to a view's reads
        self.assertEqual(priced_reads.kept_reads(view, "k", compute), 2)

    def test_a_view_without_kept_reads_computes_every_time(self):
        calls = []
        compute = lambda: calls.append(1) or len(calls)
        self.assertEqual(priced_reads.kept_reads(object(), "k", compute), 1)
        self.assertEqual(priced_reads.kept_reads(object(), "k", compute), 2)

    def test_a_wage_is_computed_again_after_a_write_to_the_memory(self):
        memory, calls = object(), []
        compute = lambda: calls.append(1) or len(calls)
        self.assertEqual(kept_wages.kept(memory, "wage", compute), 1)
        self.assertEqual(kept_wages.kept(memory, "wage", compute), 1)
        market_memory.note_written()
        self.assertEqual(kept_wages.kept(memory, "wage", compute), 2)
        self.assertEqual(kept_wages.kept(object(), "wage", compute), 3)


if __name__ == "__main__":
    unittest.main()
