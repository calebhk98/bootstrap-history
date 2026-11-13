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


class AdmittedRecipeDoesNotUndercutHeldOutputs(unittest.TestCase):
    """An admitted joint recipe prices only its new outputs: where a held technique already makes an output, the
    admitted recipe is not a producer of it (a fowling recipe's cheap mass-split fat must not reprice fat)."""

    def test_an_admitted_recipe_stops_producing_what_a_held_recipe_makes(self):
        held = {"milk": entry({"fat_kg": 1.0})}
        admitted = {"fowl": entry({"down_kg": 1.0, "fat_kg": 1.0})}
        producers = price_engine.producers_with_admitted({**held, **admitted}, frozenset(admitted))
        self.assertEqual(producers, {"fat_kg": ["milk"], "down_kg": ["fowl"]})

    def test_an_admitted_recipe_remains_a_producer_of_every_output_nothing_held_makes(self):
        held = {"milk": entry({"fat_kg": 1.0})}
        admitted = {"fowl": entry({"down_kg": 1.0, "feather_kg": 1.0})}
        producers = price_engine.producers_with_admitted({**held, **admitted}, frozenset(admitted))
        self.assertEqual(producers["down_kg"], ["fowl"])
        self.assertEqual(producers["feather_kg"], ["fowl"])

    def test_with_nothing_admitted_every_recipe_produces_all_its_outputs(self):
        entries = {"a": entry({"x_kg": 1.0, "y_kg": 1.0}), "b": entry({"y_kg": 1.0})}
        self.assertEqual(price_engine.producers_with_admitted(entries, frozenset()), {"x_kg": ["a"], "y_kg": ["a", "b"]})


if __name__ == "__main__":
    unittest.main()
