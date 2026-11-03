"""An employer whose wage payment is refused retries with what it can pay, hiring fewer hours, and posts nothing when it can pay
for none (`port_staff.bids_paid`)."""
QUICK_TOPIC = True

import unittest

from sim.markets import port_staff
from sim.refusal import Refusal


def bids_for(budget):
    """Hours bought at one unit each: the bids are the hours, the units the budget."""
    return ([budget] if budget > 0.0 else []), budget


class BidsPaid(unittest.TestCase):
    def test_a_payment_that_goes_through_posts_the_first_budgets_bids(self):
        paid = []
        bids, units, refusal = port_staff.bids_paid(bids_for, [100.0, 40.0], lambda units: paid.append(units))
        self.assertEqual((bids, units, refusal, paid), ([100.0], 100.0, None, [100.0]))

    def test_a_refused_payment_is_retried_with_the_smaller_budget_and_fewer_hours(self):
        answers = iter([Refusal("cannot_pay", "short"), None])
        bids, units, refusal = port_staff.bids_paid(bids_for, [100.0, 40.0], lambda units: next(answers))
        self.assertEqual((bids, units, refusal), ([40.0], 40.0, None))

    def test_when_every_budget_is_refused_nothing_is_posted_and_the_refusal_is_returned(self):
        bids, units, refusal = port_staff.bids_paid(bids_for, [100.0, 40.0], lambda units: Refusal("cannot_pay", "short"))
        self.assertEqual((bids, units, refusal.cause), ([], 0.0, "cannot_pay"))

    def test_a_budget_that_buys_no_hour_is_not_tried(self):
        asked = []
        bids, units, refusal = port_staff.bids_paid(bids_for, [0.0], lambda units: asked.append(units))
        self.assertEqual((bids, units, refusal, asked), ([], 0.0, None, []))


if __name__ == "__main__":
    unittest.main()
