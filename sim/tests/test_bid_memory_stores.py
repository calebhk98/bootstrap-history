"""`BidMemory.stores`: cohorts on one tile with different baskets (a hearth or not, hired work, milled grains) see
different priced needs, so each basket has its own store weights and prices; cohorts of one basket share them."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import opening_bid_memory
from sim.economy.opening_bid_memory import BidMemory


def cohort(hired_work_per_person):
    return types.SimpleNamespace(tile="t", hired_work_per_person=hired_work_per_person, milled_grains=())


class StoresPerBasket(unittest.TestCase):
    def stores(self, first, second):
        memory = BidMemory()
        with mock.patch.object(opening_bid_memory, "basket_key", lambda record, each: (each.tile, each.hired_work_per_person)):
            return memory.stores(None, first), memory.stores(None, second)

    def test_cohorts_of_one_basket_on_a_tile_share_one_store(self):
        first, second = self.stores(cohort(0.0), cohort(0.0))
        self.assertIs(first, second)

    def test_cohorts_of_different_baskets_on_a_tile_do_not(self):
        first, second = self.stores(cohort(0.0), cohort(1.0))
        self.assertIsNot(first, second)


if __name__ == "__main__":
    unittest.main()
