"""Losses scale the people bought and still in the training queue along with the slaves they are counted in, so the pools'
recount does not subtract more learners than there are slaves left."""
QUICK_TOPIC = True

import types
import unittest

from sim.labour.labour_pools import StaffPools
from sim.workforce.api import TrainingRow


class Book:
    def __init__(self, employed):
        self.employees = employed

    def set_employed(self, trade, people):
        self.employees[trade] = people

    def employed_by_trade(self):
        return self.employees

    def employed(self, trade):
        return self.employees.get(trade, 0.0)


class Trades:
    def is_craft_trade(self, trade):
        return True


def pools_over(slaves, bought_people):
    workforce = types.SimpleNamespace(
        employees={}, slaves=slaves, freedmen=0, artisans=0.0, scholars=0.0,
        training=[TrainingRow(None, bought_people, 105.0), TrainingRow("smith", 2.0, 104.0)])
    world = types.SimpleNamespace(workforce=workforce)
    return StaffPools(world, Book(workforce.employees), Trades()), workforce


class BoughtRowsFollowLosses(unittest.TestCase):
    def test_lose_share_scales_bought_rows_and_keeps_trained_rows(self):
        pools, workforce = pools_over(slaves=10, bought_people=10.0)
        pools.lose_share(0.5)
        self.assertEqual(workforce.slaves, 5)
        self.assertEqual(workforce.training[0].people, 5.0)
        self.assertEqual(workforce.training[1].people, 2.0)

    def test_trained_slaves_survive_a_loss_in_the_recount(self):
        pools, workforce = pools_over(slaves=14, bought_people=7.0)
        pools.lose_share(0.5)
        self.assertGreater(workforce.artisans, 0.0)
        self.assertAlmostEqual(workforce.artisans, (7 - 3.5) * StaffPools.TRAINED_SLAVE_ARTISAN_PRODUCTIVITY)

    def test_scale_craft_people_scales_bought_rows(self):
        pools, workforce = pools_over(slaves=10, bought_people=10.0)
        pools._scale_craft_people(0.4)
        self.assertEqual(workforce.slaves, 4)
        self.assertAlmostEqual(workforce.training[0].people, 4.0)


if __name__ == "__main__":
    unittest.main()
