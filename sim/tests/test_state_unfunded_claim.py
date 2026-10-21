"""The arithmetic of a state that cannot pay: the share of the standing need its purse covers, and the part of each
line, a group's claim among them, left unfunded (Government.pay_standing_need books these through `budget`)."""

QUICK_TOPIC = True

import unittest

from sim.agents import budget

GROUP_CLAIM_NAME = "concession: group:displaced_producers:iron"


class UnfundedClaimTests(unittest.TestCase):
    def lines(self):
        return [budget.Line("army", "requisition", wages=600.0),
                *budget.concession_lines({GROUP_CLAIM_NAME: 400.0})]

    def test_a_purse_smaller_than_the_need_leaves_the_groups_claim_partly_unfunded(self):
        lines = self.lines()
        need = sum(line.money for line in lines)
        purse = 0.25 * need
        share = budget.share_paid(need, purse)
        unfunded = budget.unfunded_by_line(lines, share)
        self.assertAlmostEqual(share, purse / need)
        self.assertAlmostEqual(unfunded[GROUP_CLAIM_NAME], 400.0 - 400.0 * purse / need)
        self.assertGreater(unfunded[GROUP_CLAIM_NAME], 0.0)

    def test_a_purse_that_covers_the_need_leaves_nothing_unfunded(self):
        lines = self.lines()
        need = sum(line.money for line in lines)
        unfunded = budget.unfunded_by_line(lines, budget.share_paid(need, 2.0 * need))
        self.assertEqual(unfunded[GROUP_CLAIM_NAME], 0.0)

    def test_what_is_borrowed_is_paid_not_unfunded(self):
        lines = self.lines()
        need = sum(line.money for line in lines)
        share = budget.share_paid(need, 0.0, borrowed=need)
        self.assertEqual(budget.unfunded_by_line(lines, share)[GROUP_CLAIM_NAME], 0.0)

    def test_the_levy_rate_is_the_unfunded_need_over_visible_income_split_by_kind_and_stops_at_the_ceiling(self):
        kinds = {"army": "requisition", "administration": "office"}
        requisition, office = budget.levy_rates({"army": 30.0, "administration": 10.0}, kinds, 1000.0)
        self.assertAlmostEqual(requisition + office, 40.0 / 1000.0)
        self.assertAlmostEqual(requisition, 3.0 * office)
        capped = budget.levy_rates({"army": 30.0, "administration": 10.0}, kinds, 1.0)
        self.assertAlmostEqual(sum(capped), budget.LEVY_RATE_CEILING)
        self.assertEqual(budget.levy_rates({"army": 0.0}, kinds, 1000.0), (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
