"""Numba port, labour clearing: the tail of every market's year (the employers a wage leaves, the hours they keep, the jobs, the wage
paid, poaching and the ask moved: `clearing_tail.clear_packed`) agrees with the plain `clearing._prepare` and `_finish`, on random
built markets with many employers; the clearings and the state they leave are compared, no game.

The kernel sums left to right where the plain code used Python's compensated `sum`, so figures agree to a relative tolerance. The
plain path itself jumps under a one-ulp nudge of its input where a rule is discrete (an employer whose bid sits at the wage, a
hire that rounds to a different count of groups); such a case is no test of the kernel and is skipped, and most cases must be
compared."""

QUICK_TOPIC = True

import math
import random
import unittest

from sim.labour.market import clearing, clearing_arrays
from sim.labour.market.records import EmployerHoursBid, copy_state
from sim.tests.test_year_speed_labour_heads import AREAS, SPECS, random_case

TOLERANCE = 1e-7


def with_many_employers(rng, scheduled):
    """A random case whose markets hold several employers each, some of them holding hours from a year before."""
    state, inputs = random_case(rng, scheduled)
    trades = list(SPECS)
    inputs.bids = list(inputs.bids) + [EmployerHoursBid("e%d" % rng.randint(0, 9), rng.choice(trades), rng.choice(AREAS),
                                                       rng.uniform(100.0, 40000.0), rng.uniform(0.4, 6.0)) for _ in range(120)]
    for bid in inputs.bids:
        if rng.random() < 0.5:
            state.hired_hours.setdefault(bid.area, {}).setdefault(bid.trade, {})[bid.employer] = rng.uniform(0.0, 30000.0)
    return state, inputs


def close(left, right):
    if left is None or right is None:
        return left is right
    return abs(left - right) <= TOLERANCE * max(1.0, abs(left), abs(right))


def plain_clear_all(state, inputs):
    real = clearing_arrays.kernel_applies
    clearing_arrays.kernel_applies = lambda _inputs: False
    try:
        return clearing.clear_all(state, inputs)
    finally:
        clearing_arrays.kernel_applies = real


def differences(got, want):
    """Names of the figures of two clearings of one market that differ."""
    found = [name for name in ("wage", "hours_offered", "hours_wanted", "hours_hired", "target_wage", "hours_held")
             if not close(getattr(got, name), getattr(want, name))]
    if set(got.hired_by_employer) != set(want.hired_by_employer) or not all(
            close(got.hired_by_employer[each], want.hired_by_employer[each]) for each in want.hired_by_employer if each in got.hired_by_employer):
        found.append("hired_by_employer")
    if got.demand != want.demand:
        found.append("demand")
    return found


class TheTailOfEveryMarketAgreesWithThePlainFunctions(unittest.TestCase):

    def compare(self, scheduled, seed):
        rng = random.Random(seed)
        compared = skipped = employers = 0
        for _case in range(25):
            state, inputs = with_many_employers(rng, scheduled)
            fast_state, plain_state, again_state = copy_state(state), copy_state(state), copy_state(state)
            fast = clearing.clear_all(fast_state, inputs)
            plain = plain_clear_all(plain_state, inputs)
            for area, by_trade in again_state.workers.items():      # one ulp more of everything the plain path starts from
                for trade, bands in by_trade.items():
                    by_trade[trade] = [math.nextafter(each, math.inf) for each in bands]
            nudged = plain_clear_all(again_state, inputs)
            self.assertEqual([(each.trade, each.area) for each in fast], [(each.trade, each.area) for each in plain])
            for got, want, other in zip(fast, plain, nudged):
                if differences(want, other):
                    skipped += 1
                    continue
                compared += 1
                employers += len(want.hired_by_employer)
                self.assertEqual(differences(got, want), [], "%s: kernel %r, plain %r" % ((want.trade, want.area), got, want))
                for table in ("wages", "asks"):
                    self.assertTrue(close(getattr(fast_state, table)[want.area][want.trade], getattr(plain_state, table)[want.area][want.trade]),
                                    "%s of %s" % (table, (want.trade, want.area)))
                kept_fast, kept_plain = fast_state.hired_hours[want.area][want.trade], plain_state.hired_hours[want.area][want.trade]
                self.assertEqual(set(kept_fast), set(kept_plain))
                self.assertTrue(all(close(kept_fast[each], kept_plain[each]) for each in kept_plain))
        self.assertGreater(compared, 10 * skipped)
        self.assertGreater(compared, 200)
        self.assertGreater(employers, 200)

    def test_every_worker_sells_a_whole_year(self):
        self.compare(False, 21)

    def test_hours_sold_follow_a_schedule(self):
        self.compare(True, 22)


if __name__ == "__main__":
    unittest.main()
