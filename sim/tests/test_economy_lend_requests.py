"""Two requests by one borrower in a clearing both count in what it asked."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.economy import lend_requests


def request(borrower, amount):
    return SimpleNamespace(borrower=borrower, amount=amount)


class AskedAndWorthTests(unittest.TestCase):
    def test_a_borrowers_two_requests_add_up(self):
        asked, _worth = lend_requests.asked_and_worth([request("a", 30.0), request("b", 5.0), request("a", 10.0)], lambda each: 1.0)
        self.assertEqual(asked, {"a": 40.0, "b": 5.0})

    def test_worth_is_the_mean_weighted_by_amount(self):
        worths = {30.0: 2.0, 10.0: 6.0}
        _asked, worth = lend_requests.asked_and_worth([request("a", 30.0), request("a", 10.0)], lambda each: worths[each.amount])
        self.assertAlmostEqual(worth["a"], 3.0)

    def test_a_borrower_with_no_plant_has_no_worth(self):
        asked, worth = lend_requests.asked_and_worth([request("a", 30.0)], lambda each: None)
        self.assertEqual(asked, {"a": 30.0})
        self.assertEqual(worth, {})


if __name__ == "__main__":
    unittest.main()
