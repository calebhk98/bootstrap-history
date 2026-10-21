"""Complaint 538: a producer whose run costs nothing (cleared land) and whose only output is piling up unsold
is held to what it expects to sell; an output that is not piling up is what can make a costless run pay on."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy import producers
from sim.economy.types import Recipe
from sim.tests.test_joint_recipe_runs_on_value import View

CLEARING = Recipe("clearing", {"ground": 1.0}, {}, {})
JOINT_FREE = Recipe("joint_free", {"ground": 1.0, "timber": 1.0}, {}, {})


def clearer(recipe_id="clearing"):
    return producers.Producer(agent_id="c1", owner="lord", recipe_id=recipe_id, tile="t", capacity_runs=10.0,
                              last_runs=5.0, expected_sales=0.5, expected_prices={"ground": 100.0})


class CostlessRunStockGateTests(unittest.TestCase):
    def test_a_costless_run_with_one_unsold_output_is_stopped_by_its_stock(self):
        view = View({"ground": 200.0}, {"ground": 100.0})
        runs = producers.runs_for_stock(clearer(), CLEARING, view, 0.0, {"ground": 100.0})
        self.assertEqual(runs, 0.0)

    def test_a_costless_run_with_an_output_that_is_not_piling_up_keeps_running(self):
        view = View({"ground": 200.0}, {"ground": 100.0, "timber": 5.0})
        runs = producers.runs_for_stock(clearer("joint_free"), JOINT_FREE, view, 0.0, {"ground": 100.0, "timber": 5.0})
        self.assertTrue(math.isinf(runs))


if __name__ == "__main__":
    unittest.main()
