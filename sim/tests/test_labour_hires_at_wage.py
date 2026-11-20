"""hires_at_wage: the hours each labour bid wants at a wage and the hours it is given of those offered."""

QUICK_TOPIC = True

import unittest

from sim.labour.market import clearing
from sim.labour.market.hires_at_wage import by_employer, hires_at_wage, ranks_of, wanted_at_wage
from sim.labour.market.records import EmployerHoursBid

FLOOR = 1.0


class WantedAtWage(unittest.TestCase):
    def test_a_bid_capped_under_the_floor_wants_nothing(self):
        self.assertEqual(wanted_at_wage(0.5, FLOOR, [0.8], [100.0]), [0.0])

    def test_at_or_under_the_lower_end_a_bid_wants_all_its_hours(self):
        # caps 2 and 4 over a floor of 1: the second bid's interval is 2 to 4
        wanted = wanted_at_wage(2.0, FLOOR, [2.0, 4.0], [100.0, 60.0])
        self.assertEqual(wanted[1], 60.0)
        self.assertEqual(wanted_at_wage(1.0, FLOOR, [2.0], [100.0]), [100.0])
        self.assertEqual(wanted_at_wage(0.5, FLOOR, [2.0], [100.0]), [100.0])

    def test_at_its_cap_or_above_a_bid_wants_none(self):
        self.assertEqual(wanted_at_wage(2.0, FLOOR, [2.0], [100.0]), [0.0])
        self.assertEqual(wanted_at_wage(3.0, FLOOR, [2.0], [100.0]), [0.0])

    def test_halfway_between_the_next_lower_cap_and_its_cap_wants_half(self):
        wanted = wanted_at_wage(3.0, FLOOR, [2.0, 4.0], [100.0, 60.0])     # 3 is halfway from 2 to 4
        self.assertAlmostEqual(wanted[1], 60.0 * (4.0 - 3.0) / (4.0 - 2.0))
        self.assertAlmostEqual(wanted[0], 0.0)
        wanted_low = wanted_at_wage(1.5, FLOOR, [2.0], [100.0])           # halfway from the floor 1 to the cap 2
        self.assertAlmostEqual(wanted_low[0], 50.0)

    def test_two_bids_with_the_same_cap_share_the_same_interval(self):
        wanted = wanted_at_wage(1.5, FLOOR, [2.0, 2.0], [100.0, 40.0])
        self.assertAlmostEqual(wanted[0], 100.0 * 0.5)
        self.assertAlmostEqual(wanted[1], 40.0 * 0.5)

    def test_total_agrees_with_the_clearing_schedule(self):
        # the cross-check's subject is that this function and clearing.hours_wanted_at describe one schedule
        caps = [2.0, 4.0, 2.0, 0.5]
        hours = [100.0, 60.0, 40.0, 70.0]
        bids = [EmployerHoursBid("e%d" % i, "digger", "vale", hours[i], caps[i]) for i in range(len(caps))]
        intervals = clearing.demand_intervals(FLOOR, bids)
        for wage in (0.5, 1.0, 1.25, 2.0, 2.5, 3.0, 4.0, 5.0):
            self.assertAlmostEqual(sum(wanted_at_wage(wage, FLOOR, caps, hours)), clearing.hours_wanted_at(wage, intervals))


class HiresAtWage(unittest.TestCase):
    def test_offered_above_the_total_wanted_gives_each_bid_what_it_wants(self):
        self.assertEqual(hires_at_wage(500.0, [100.0, 40.0]), [100.0, 40.0])

    def test_offered_below_cuts_every_bid_by_the_same_share(self):
        hires = hires_at_wage(70.0, [100.0, 40.0])
        share = 70.0 / (100.0 + 40.0)
        self.assertAlmostEqual(hires[0], 100.0 * share)
        self.assertAlmostEqual(hires[1], 40.0 * share)
        self.assertAlmostEqual(sum(hires), 70.0)

    def test_nothing_offered_gives_zeros(self):
        self.assertEqual(hires_at_wage(0.0, [100.0, 40.0]), [0.0, 0.0])

    def test_nothing_wanted_gives_zeros(self):
        self.assertEqual(hires_at_wage(100.0, [0.0, 0.0]), [0.0, 0.0])


class ByEmployer(unittest.TestCase):
    def test_hours_are_summed_per_employer_in_name_order(self):
        total = by_employer(["b", "a", "b"], [5.0, 2.0, 7.0])
        self.assertEqual(total, {"a": 2.0, "b": 12.0})
        self.assertEqual(list(total), ["a", "b"])


class RanksOf(unittest.TestCase):
    def test_hours_are_summed_and_standing_is_the_highest_cap(self):
        hours, standing = ranks_of(["a", "a", "b"], [2.0, 3.0, 1.5], [10.0, 20.0, 5.0])
        self.assertEqual(hours, {"a": 30.0, "b": 5.0})
        self.assertEqual(standing, {"a": 3.0, "b": 1.5})

    def test_a_bid_wanting_nothing_is_left_out(self):
        hours, standing = ranks_of(["a", "b"], [2.0, 3.0], [10.0, 0.0])
        self.assertEqual(hours, {"a": 10.0})
        self.assertEqual(standing, {"a": 2.0})


if __name__ == "__main__":
    unittest.main()
