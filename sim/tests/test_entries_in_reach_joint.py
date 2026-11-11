"""`entries_in_reach` on a joint herd recipe whose co-product the society already makes: the recipe still brings the new
output into reach (Complaints/558: a horse herd makes meat a society holds and the draught animal it does not)."""

import unittest

from sim.prices import prices as price_engine

QUICK_TOPIC = True
CIVILISATION_GATE = "gate_not_in_the_tree"


def entry(outputs):
    return {"outputs": outputs, "inputs": {}, "labour_hours": {"labourer": 1.0}, "requires_node": CIVILISATION_GATE}


class JointRecipeInReachTests(unittest.TestCase):

    def test_a_joint_recipe_is_in_reach_when_one_output_is_new_and_the_other_is_already_made(self):
        entries = {"herd": entry({"meat_kg": 1.0, "draught_animal_kg": 1.0})}
        reach = price_engine.entries_in_reach(set(), frozenset(), {"meat_kg"}, entries)
        self.assertIn("herd", reach)

    def test_a_recipe_whose_every_output_is_already_made_is_not_in_reach(self):
        entries = {"herd": entry({"meat_kg": 1.0, "hide_kg": 1.0})}
        reach = price_engine.entries_in_reach(set(), frozenset(), {"meat_kg", "hide_kg"}, entries)
        self.assertNotIn("herd", reach)

    def test_the_nearest_recipe_for_the_new_output_wins_whatever_the_old_output_is(self):
        entries = {"a_herd": entry({"meat_kg": 1.0, "draught_animal_kg": 1.0}),
                   "b_herd": entry({"meat_kg": 1.0, "draught_animal_kg": 2.0})}
        reach = price_engine.entries_in_reach(set(), frozenset(), {"meat_kg"}, entries)
        self.assertEqual(sorted(reach), ["a_herd"])


if __name__ == "__main__":
    unittest.main()
