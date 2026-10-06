"""A trade whose posts are all filled but whose pay is far over its ask still draws workers."""

QUICK_TOPIC = True

import unittest

from sim.economy import labour_asks


class FilledOverpaidTradeTests(unittest.TestCase):
    def test_a_filled_trade_paid_far_over_its_ask_draws_workers(self):
        moved = labour_asks.follow_pay({"labourer": 1000.0, "smith": 0.36}, {"labourer": 1.0, "smith": 2000.0},
                                       {"labourer": 1000.0, "smith": 0.36})
        self.assertGreater(moved["smith"], 0.36)

    def test_a_filled_trade_paid_its_ask_draws_nobody(self):
        workforce = {"labourer": 1000.0, "smith": 0.36}
        self.assertEqual(labour_asks.follow_pay(workforce, {"labourer": 1.0, "smith": 1.0},
                                                {"labourer": 1000.0, "smith": 0.36}), workforce)


if __name__ == "__main__":
    unittest.main()
