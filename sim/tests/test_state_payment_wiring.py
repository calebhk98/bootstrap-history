"""Complaint 185, Complaint 640: the founder's household pays the state through the ledger: the polity module's `pay_state` sends
the ledger the treasury and the sum, and the ledger books the loss as the treasury's gain by purpose (test_ledger_commands)."""
QUICK_TOPIC = True

import unittest
from contextlib import nullcontext
from types import SimpleNamespace

from sim.ledger.api import PayActorFromHousehold
from sim.tests import module_harness, polity_host


class PayState(unittest.TestCase):
    def test_the_household_pays_the_treasury_the_sum_with_its_purpose(self):
        module = polity_host.build(state_treasury=SimpleNamespace(actor_id="government:rome_100ad"), transfer_listening=nullcontext)
        module.pay_state(300.0, {"requisition": 200.0, "office": 100.0})
        self.assertEqual(module_harness.sent(module), [PayActorFromHousehold("government:rome_100ad", 300.0, {"requisition": 200.0, "office": 100.0})])


if __name__ == "__main__":
    unittest.main()
