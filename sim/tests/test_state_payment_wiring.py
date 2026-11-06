"""Complaint 185, Complaint 640: the founder's household pays the state through the ledger: the polity module's `pay_state` sends
the ledger the treasury and the sum, and the ledger books the loss as the treasury's gain by purpose (test_ledger_commands)."""
QUICK_TOPIC = True

import unittest
from contextlib import nullcontext
from types import SimpleNamespace

from sim.ledger.api import PayActorFromHousehold
from sim.refusal import Refusal
from sim.tests import module_harness, polity_host


class PayState(unittest.TestCase):
    def test_the_household_pays_the_treasury_the_sum_with_its_purpose(self):
        module = polity_host.build(state_treasury=SimpleNamespace(actor_id="government:rome_100ad"), transfer_listening=nullcontext)
        module.pay_state(300.0, {"requisition": 200.0, "office": 100.0})
        self.assertEqual(module_harness.sent(module), [PayActorFromHousehold("government:rome_100ad", 300.0, {"requisition": 200.0, "office": 100.0})])

    def test_a_payment_the_household_cannot_cover_comes_back_as_the_refusal_and_is_logged_unpaid(self):
        refusal = Refusal("cannot_pay", "no lender holds the funds", amount=300.0)
        module = polity_host.build(state_treasury=SimpleNamespace(actor_id="government:rome_100ad"), transfer_listening=nullcontext,
                                   answers={PayActorFromHousehold: refusal})
        self.assertIs(module.pay_state(300.0, "gift"), refusal)
        event = module_harness.sent(module)[-1]
        self.assertEqual((event.kind, event.facts["cause"], event.facts["amount"]), ("unpaid_charge", "cannot_pay", 300.0))

    def test_a_sum_refused_is_not_counted_as_paid(self):
        module = polity_host.build(acting_balance=lambda: 500.0, answers={PayActorFromHousehold: Refusal("cannot_pay", "x")},
                                   state_treasury=SimpleNamespace(actor_id="government:x"), transfer_listening=nullcontext)
        self.assertEqual(module.pay_state_sum(300.0, "gift"), 0.0)


if __name__ == "__main__":
    unittest.main()
