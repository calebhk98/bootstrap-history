"""`opening_runs.required_runs` reaches a fixed point where a joint recipe's co-product is used by a rival maker of its main
output (Complaint 981): silver comes off a lead smelt, a cheaper silver recipe needs lead, and lead is made only by that
smelt. The runs must not depend on how many passes were allowed. Hand-built recipes; no game."""
import unittest

import numpy as np

from sim.economy import opening_runs, opening_runs_pack
from sim.economy.types import Recipe

QUICK_TOPIC = True

RECIPES = {
    "dig_ore": Recipe("dig_ore", {"ore": 1000.0}, {}, {"miner": 1.0}),
    "dig_gossan": Recipe("dig_gossan", {"gossan": 1000.0}, {}, {"miner": 1.0}),
    "smelt_joint": Recipe("smelt_joint", {"lead": 1000.0, "silver": 2.0}, {"ore": 8000.0}, {"smelter": 1.0}),
    "smelt_gossan": Recipe("smelt_gossan", {"silver": 1000.0}, {"gossan": 2000000.0, "lead": 25000.0}, {"smelter": 1.0}),
}
RANKED = {"silver": ["smelt_gossan", "smelt_joint"], "lead": ["smelt_joint"], "ore": ["dig_ore"], "gossan": ["dig_gossan"]}
MAIN = {"dig_ore": "ore", "dig_gossan": "gossan", "smelt_joint": "silver", "smelt_gossan": "silver"}
DEMAND = {"town": {"silver": 180000.0, "lead": 300000.0}}
# the gossan smelt runs as far as the lead of the silver-driven joint smelts goes, and those make the silver it cannot:
# gossan runs = joint runs for silver * lead a run / lead a gossan run, joint runs for silver = (silver wanted - gossan silver) / silver a run
GOSSAN_RUNS = 3600.0 / 21.0
JOINT_RUNS_FOR_SILVER = (180000.0 - 1000.0 * GOSSAN_RUNS) / 2.0
JOINT_RUNS = (25000.0 * GOSSAN_RUNS + 300000.0) / 1000.0      # every user of lead is supplied


class RequiredRunsSettleTests(unittest.TestCase):
    def test_the_runs_are_the_fixed_point(self):
        runs = opening_runs.required_runs(DEMAND, RANKED, RECIPES, None, None, MAIN)
        self.assertAlmostEqual(runs["smelt_gossan"], GOSSAN_RUNS, delta=1e-6 * GOSSAN_RUNS)
        self.assertAlmostEqual(runs["smelt_joint"], JOINT_RUNS, delta=1e-6 * JOINT_RUNS)
        self.assertGreater(JOINT_RUNS, JOINT_RUNS_FOR_SILVER)
        self.assertAlmostEqual(runs["dig_gossan"], 2000.0 * GOSSAN_RUNS, delta=1e-6 * 2000.0 * GOSSAN_RUNS)
        self.assertAlmostEqual(runs["dig_ore"], 8.0 * JOINT_RUNS, delta=1e-6 * 8.0 * JOINT_RUNS)

    def test_every_input_the_runs_use_is_made(self):
        runs = opening_runs.required_runs(DEMAND, RANKED, RECIPES, None, None, MAIN)
        required = opening_runs.required_quantities(DEMAND, runs, RECIPES)
        for good, quantity in required.items():
            made = sum(count * RECIPES[recipe_id].outputs.get(good, 0.0) for recipe_id, count in runs.items())
            self.assertGreaterEqual(made, quantity * (1.0 - 1e-6), good)

    def test_one_more_pass_changes_nothing(self):
        bound = opening_runs.INPUT_OUTPUT_PASSES
        try:
            answers = []
            for extra in range(3):
                opening_runs.INPUT_OUTPUT_PASSES = bound + extra
                answers.append(opening_runs.required_runs(DEMAND, RANKED, RECIPES, None, None, MAIN))
        finally:
            opening_runs.INPUT_OUTPUT_PASSES = bound
        for recipe_id in RECIPES:
            for other in answers[1:]:
                self.assertAlmostEqual(other.get(recipe_id, 0.0), answers[0].get(recipe_id, 0.0),
                                       delta=1e-6 * max(1.0, answers[0].get(recipe_id, 0.0)), msg=recipe_id)

    def test_the_kernel_settles_on_the_same_runs(self):
        solver = opening_runs_pack.RunSolver(RECIPES, RANKED, {}, {}, MAIN, {"miner": 1.0, "smelter": 1.0})
        national = np.zeros(len(solver.goods))
        for good, quantity in DEMAND["town"].items():
            national[solver.good_position[good]] = quantity
        runs = solver.runs_by_recipe(solver.runs(national))
        expected = opening_runs.required_runs(DEMAND, RANKED, RECIPES, None, None, MAIN)
        for recipe_id in RECIPES:
            self.assertAlmostEqual(runs[recipe_id], expected[recipe_id], delta=1e-6 * expected[recipe_id], msg=recipe_id)


if __name__ == "__main__":
    unittest.main()
