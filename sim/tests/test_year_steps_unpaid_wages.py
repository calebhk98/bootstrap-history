"""pay_wages_or_log: wages the acting seat cannot pay are logged as an unpaid charge with the refusal's cause, never dropped."""

QUICK_TOPIC = True

import unittest

from sim.engine import year_steps
from sim.ledger.api import PayWages, UNPAID_CHARGE_KIND
from sim.refusal import Refusal


class PayWagesOrLog(unittest.TestCase):
    def test_paid_wages_send_one_command_and_log_nothing(self):
        sent = []
        self.assertIsNone(year_steps.pay_wages_or_log(lambda command: sent.append(command), 40.0, "living costs"))
        self.assertEqual(sent, [PayWages(40.0, "living costs")])

    def test_a_refused_payment_is_logged_with_its_cause_and_returned(self):
        sent = []

        def send(command):
            sent.append(command)
            if isinstance(command, PayWages):
                return Refusal("insufficient_funds", "no money")

        refusal = year_steps.pay_wages_or_log(send, 40.0, "living costs")
        self.assertEqual(refusal.cause, "insufficient_funds")
        [_paid, event] = sent
        self.assertEqual(event.kind, UNPAID_CHARGE_KIND)
        self.assertEqual((event.facts["amount"], event.facts["cause"]), (40.0, "insufficient_funds"))


if __name__ == "__main__":
    unittest.main()
