"""A payment's purpose is a credit claim only when it names one: an empty purpose is not a claim on a debtor, so the
coin it carries moves."""

QUICK_TOPIC = True

import unittest

from sim.coin.rules import is_credit


class IsCredit(unittest.TestCase):
    def test_an_empty_purpose_is_not_a_credit_claim(self):
        self.assertFalse(is_credit({}))

    def test_a_purpose_of_only_credit_labels_is_a_credit_claim(self):
        self.assertTrue(is_credit({"interest": 1.0, "loan": 2.0}))
        self.assertTrue(is_credit("loan repayment"))

    def test_a_mixed_purpose_is_not_a_credit_claim(self):
        self.assertFalse(is_credit({"interest": 1.0, "wages": 2.0}))
