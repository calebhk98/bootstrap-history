"""The engine's hours by trade have one owner: the labour core's people when the agent economy runs, the recipe
graph's need when it does not (Complaint 640: rules on built inputs). There is no separate workforce that moves hours between trades."""
QUICK_TOPIC = True

import unittest

from .harness import *  # noqa: F401,F403
from sim.labour import labour_allocation, labour_market

FARM = labour_allocation.FARM_TRADE
HOURS_PER_WORKER = labour_allocation.HOURS_PER_FARM_WORKER_YEAR
REST = 1000.0 * HOURS_PER_WORKER


class SharesFromPeopleTests(unittest.TestCase):

    def test_a_trade_with_more_people_has_more_hours(self):
        before = labour_allocation.shares_from_people({"smith": 10.0, "weaver": 10.0}, "labourer", REST)
        after = labour_allocation.shares_from_people({"smith": 500.0, "weaver": 10.0}, "labourer", REST)
        self.assertGreater(after["smith"], 5.0 * before["smith"])

    def test_shares_add_up_to_one_and_the_pool_trade_takes_what_the_specialists_leave(self):
        shares = labour_allocation.shares_from_people({"smith": 100.0, "weaver": 300.0}, "labourer", REST)
        self.assertAlmostEqual(sum(shares.values()), 1.0, places=12)
        self.assertAlmostEqual(shares["smith"], 100.0 / 1000.0, places=12)
        self.assertAlmostEqual(shares["labourer"], 1.0 - 400.0 / 1000.0, places=12)

    def test_specialists_never_take_more_than_all_the_hours(self):
        shares = labour_allocation.shares_from_people({"smith": 5000.0}, "labourer", REST)
        self.assertAlmostEqual(shares["smith"], 1.0, places=12)
        self.assertAlmostEqual(shares["labourer"], 0.0, places=12)

    def test_farm_and_pool_headcounts_do_not_count_as_specialists(self):
        shares = labour_allocation.shares_from_people({FARM: 9000.0, "labourer": 9000.0, "smith": 100.0}, "labourer", REST)
        self.assertEqual(set(shares), {"smith", "labourer"})
        self.assertAlmostEqual(shares["smith"], 100.0 / 1000.0, places=12)

    def test_no_people_or_no_hours_gives_no_answer_so_the_recipe_need_applies(self):
        self.assertIsNone(labour_allocation.shares_from_people({}, "labourer", REST))
        self.assertIsNone(labour_allocation.shares_from_people({"smith": 0.0}, "labourer", REST))
        self.assertIsNone(labour_allocation.shares_from_people({"smith": 10.0}, "labourer", 0.0))


class NoSecondWorkforceTests(unittest.TestCase):

    def test_no_second_workforce_moves_hours_between_trades(self):
        self.assertFalse(hasattr(labour_market, "Workforce"))
        self.assertFalse(hasattr(labour_allocation, "reallocate"))


if __name__ == "__main__":
    unittest.main()
