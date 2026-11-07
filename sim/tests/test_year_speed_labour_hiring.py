"""Numba port, labour clearing: `applications.hire_markets` (the hiring kernel) agrees with the plain Python rounds kept in
`labour_hiring_reference`, on random inputs; no game.

The kernel sums left to right and takes pay tiers in rank order, where the plain code summed with Python's compensated
`sum` and took tiers in set order, so figures agree to a relative tolerance, not bit for bit. A rule with a knife edge
(an employer filled to within rounding either posts a vacancy of a few ulps or none, and a poster changes every
group's reach) turns a one-ulp change of input into a different market; a case where the plain code itself does so is
no test of the kernel and is skipped (`is_stable`)."""

QUICK_TOPIC = True

import math
import random
import unittest

from sim.labour.market import applications
from sim.tests import labour_hiring_reference as reference

TOLERANCE = 1e-9     # a few ulps per sum, carried through twelve rounds of rates that divide by small differences


def random_job(rng):
    names = ["e%02d" % i for i in range(rng.randint(1, 14))]
    return dict(
        hired={name: rng.choice([0.0, rng.uniform(0.0, 3000.0)]) for name in names},
        kept={name: rng.uniform(0.0, 3000.0) for name in names},
        wanted={name: rng.uniform(0.0, 4000.0) for name in names},
        offers={name: rng.choice([1.0, 1.5, rng.uniform(0.5, 3.0)]) for name in names},
        pool=rng.uniform(0.0, 9000.0), ask=rng.uniform(0.5, 3.5), floor=rng.uniform(0.1, 1.0),
        ceilings=rng.choice([None, None, {name: rng.uniform(1.0, 4.0) for name in names}]))


def is_stable(spec):
    """Whether the plain rounds give the same answer, within the tolerance, when the pool is one ulp larger."""
    runs = []
    for pool in (spec["pool"], math.nextafter(spec["pool"], math.inf)):
        copy = {name: dict(spec[name]) for name in ("hired", "kept", "offers")}
        runs.append(reference.hire_through_rounds(copy["hired"], copy["kept"], spec["wanted"], copy["offers"], pool,
                                                  spec["ask"], spec["floor"], spec["ceilings"]))
    first, second = runs
    return sorted(first) == sorted(second) and all(abs(first[key] - second[key]) <= TOLERANCE * max(1.0, abs(first[key])) for key in first)


def assert_close(test, got, expected):
    test.assertEqual(sorted(got), sorted(expected))
    for key in expected:
        test.assertAlmostEqual(got[key], expected[key], delta=TOLERANCE * max(1.0, abs(expected[key])))


class HiringKernelAgreesWithThePlainRounds(unittest.TestCase):

    def test_one_market_at_a_time(self):
        rng = random.Random(11)
        compared = 0
        for _case in range(120):
            spec = random_job(rng)
            if not is_stable(spec):
                continue
            compared += 1
            fast = {name: dict(spec[name]) for name in ("hired", "kept", "offers")}
            plain = {name: dict(spec[name]) for name in ("hired", "kept", "offers")}
            arguments = (spec["pool"], spec["ask"], spec["floor"], spec["ceilings"])
            got = applications.hire_through_rounds(fast["hired"], fast["kept"], spec["wanted"], fast["offers"], *arguments)
            expected = reference.hire_through_rounds(plain["hired"], plain["kept"], spec["wanted"], plain["offers"], *arguments)
            assert_close(self, got, expected)
            for name in fast:
                assert_close(self, fast[name], plain[name])
        self.assertGreater(compared, 80)

    def test_many_markets_in_one_call_equal_each_alone(self):
        rng = random.Random(3)
        specs = [random_job(rng) for _case in range(25)]
        jobs = [applications.HireJob(dict(spec["hired"]), dict(spec["kept"]), spec["wanted"], dict(spec["offers"]),
                                     spec["pool"], spec["ask"], spec["floor"], spec["ceilings"]) for spec in specs]
        applications.hire_markets(jobs)
        for spec, job in zip(specs, jobs):
            alone = (dict(spec["hired"]), dict(spec["kept"]), dict(spec["offers"]))
            taken = applications.hire_through_rounds(alone[0], alone[1], spec["wanted"], alone[2], spec["pool"], spec["ask"],
                                                     spec["floor"], spec["ceilings"])
            self.assertEqual(job.taken, taken)
            self.assertEqual((job.hired, job.kept, job.offers), alone)


if __name__ == "__main__":
    unittest.main()
