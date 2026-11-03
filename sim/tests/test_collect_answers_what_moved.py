"""`Government.collect` answers the amount that reached the treasury, not the levy it asked for."""

QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.agents.api import ActorRecord
from sim.agents.government import Government


class Collect(unittest.TestCase):
    def test_a_payer_whose_payment_falls_short_after_the_gate_is_counted_at_what_it_paid(self):
        treasury = Government("government:home", ActorRecord(kind="government"))
        treasury.assess = lambda payer, taxable, world: (10.0, {"requisition": 0.0, "office": 10.0})
        with mock.patch("sim.agents.government.ledger.payable", return_value=10.0), \
                mock.patch("sim.agents.government.ledger.pay_up_to", return_value=4.0):
            self.assertEqual(treasury.collect(object(), 100.0, object()), 4.0)

    def test_a_levy_of_nothing_collects_nothing(self):
        treasury = Government("government:home", ActorRecord(kind="government"))
        treasury.assess = lambda payer, taxable, world: (0.0, {"requisition": 0.0, "office": 0.0})
        self.assertEqual(treasury.collect(object(), 100.0, object()), 0.0)


if __name__ == "__main__":
    unittest.main()
