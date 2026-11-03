"""A seat's own credit line given back among the lenders' capacities (`line_claim.with_own_claim`)."""
QUICK_TOPIC = True

import unittest

from sim.actors.line_claim import with_own_claim


class OwnClaim(unittest.TestCase):
    rows = [("cohort:a", 10.0, 2.0, 10.0, 0.04), ("bank:b", 5.0, 0.0, 5.0, 0.09)]

    def test_the_claim_returns_to_the_cheapest_lender_up_to_what_it_offered_beyond_its_capacity(self):
        self.assertEqual([row[2] for row in with_own_claim(self.rows, 9.0)], [10.0, 1.0])

    def test_no_claim_leaves_the_capacities(self):
        self.assertEqual(with_own_claim(self.rows, 0.0), self.rows)

    def test_a_claim_larger_than_every_lenders_share_never_lifts_a_capacity_above_its_offer(self):
        self.assertEqual([row[2] for row in with_own_claim(self.rows, 100.0)], [10.0, 5.0])


if __name__ == "__main__":
    unittest.main()
