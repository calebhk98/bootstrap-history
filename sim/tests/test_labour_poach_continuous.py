"""Complaint 473: hours drawn off a lower employer by a higher one (`clearing.poach`, `on_the_job_loss_share`) change by a
hair when a standing changes by a hair. Employers of one trade often stand level (their bids are capped at one figure), so
a rule that drew a tenth of a rival's hours at any gap, and none at none, let rounding decide who lost them."""

QUICK_TOPIC = True

import unittest

from sim.labour.market.clearing import on_the_job_loss_share, poach

HAIR = 1e-12


class LossShareRisesFromNothing(unittest.TestCase):
    def test_a_rival_a_hair_higher_draws_off_a_hair(self):
        self.assertLess(on_the_job_loss_share(100.0, 100.0 * (1.0 + 1e-9)), 1e-6)

    def test_the_share_grows_with_the_gap(self):
        shares = [on_the_job_loss_share(100.0, rival) for rival in (100.0, 101.0, 110.0, 150.0, 300.0)]
        self.assertEqual(shares[0], 0.0)
        self.assertEqual(shares, sorted(shares))
        self.assertGreater(shares[1], 0.0)

    def test_no_more_than_every_hour_leaves(self):
        self.assertEqual(on_the_job_loss_share(1.0, 1e9), 1.0)
        self.assertEqual(on_the_job_loss_share(0.0, 5.0), 1.0)


class PoachingIsContinuousInStanding(unittest.TestCase):
    def test_level_employers_a_hair_apart_exchange_next_to_nothing(self):
        hired = {"holder": 1000.0, "short": 0.0}
        poach(hired, {"holder": 1000.0, "short": 500.0}, {"holder": 3.0, "short": 3.0 * (1.0 + HAIR)})
        self.assertAlmostEqual(hired["holder"], 1000.0, places=6)
        self.assertAlmostEqual(hired["short"], 0.0, places=6)

    def test_which_of_two_level_employers_is_a_hair_higher_does_not_matter(self):
        wanted = {"low": 1000.0, "first": 600.0, "second": 600.0}
        splits = []
        for first, second in ((3.0, 3.0 * (1.0 + HAIR)), (3.0 * (1.0 + HAIR), 3.0)):
            hired = {"low": 1000.0, "first": 100.0, "second": 100.0}
            poach(hired, wanted, {"low": 1.0, "first": first, "second": second})
            splits.append(hired)
        for name in wanted:
            self.assertAlmostEqual(splits[0][name], splits[1][name], places=6)
        self.assertAlmostEqual(splits[0]["first"], splits[0]["second"], places=6)
        self.assertGreater(splits[0]["first"], 100.0)

    def test_the_higher_standing_draws_more(self):
        hired = {"low": 1000.0, "higher": 0.0, "highest": 0.0}
        poach(hired, {"low": 1000.0, "higher": 5000.0, "highest": 5000.0}, {"low": 1.0, "higher": 1.5, "highest": 2.5})
        self.assertGreater(hired["highest"], hired["higher"])
        self.assertGreater(hired["higher"], 0.0)


class PoachingKeepsTheHours(unittest.TestCase):
    def test_hours_are_moved_not_made(self):
        hired = {"a": 300.0, "b": 400.0, "c": 20.0, "d": 0.0}
        poach(hired, {"a": 300.0, "b": 900.0, "c": 800.0, "d": 700.0}, {"a": 1.0, "b": 1.4, "c": 2.2, "d": 9.0})
        self.assertAlmostEqual(sum(hired.values()), 720.0, places=9)

    def test_an_employer_asked_for_more_than_it_holds_gives_no_more_than_that(self):
        hired = {"low": 10.0}
        wanted = {"low": 10.0}
        standing = {"low": 1.0}
        for number in range(30):
            name = "rich%02d" % number
            hired[name], wanted[name], standing[name] = 0.0, 1000.0, 50.0 + number
        poach(hired, wanted, standing)
        self.assertGreaterEqual(hired["low"], 0.0)
        self.assertAlmostEqual(sum(hired.values()), 10.0, places=9)

    def test_nobody_is_drawn_past_what_it_wants(self):
        hired = {"low": 1000.0, "nearly": 495.0}
        poach(hired, {"low": 1000.0, "nearly": 500.0}, {"low": 1.0, "nearly": 4.0})
        self.assertAlmostEqual(hired["nearly"], 500.0, places=9)
        self.assertAlmostEqual(hired["low"], 995.0, places=9)


if __name__ == "__main__":
    unittest.main()
