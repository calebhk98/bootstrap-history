"""Which built nodes a loss event may take (Complaints 259): not inherited, not a measured goal (a measurement cannot be
forgotten, so it is never announced twice), and by default not a dispersed corpus."""
import unittest

from sim.knowledge.rules import losable_node_ids

QUICK_TOPIC = True

NODES = {"plain": {}, "inherited": {}, "goal": {"win_condition": True}, "copies": {}, "other": {}}
EVERYTHING = {"plain", "inherited", "goal", "copies", "other"}


def losable(held, granted=(), dispersed=(), keep_dispersed=True):
    return losable_node_ids(held, set(granted), NODES, keep_dispersed, lambda node_id: node_id in set(dispersed))


class LosableNodes(unittest.TestCase):

    def test_a_measured_goal_is_never_losable(self):
        self.assertNotIn("goal", losable(EVERYTHING))

    def test_an_inherited_node_is_never_losable(self):
        self.assertNotIn("inherited", losable(EVERYTHING, granted={"inherited"}))

    def test_a_dispersed_corpus_is_kept_by_default_and_losable_when_asked(self):
        self.assertNotIn("copies", losable(EVERYTHING, dispersed={"copies"}))
        self.assertIn("copies", losable(EVERYTHING, dispersed={"copies"}, keep_dispersed=False))

    def test_what_is_left_is_every_other_built_node_in_order(self):
        self.assertEqual(losable(EVERYTHING, granted={"inherited"}, dispersed={"copies"}), ["other", "plain"])

    def test_an_unbuilt_node_is_not_losable(self):
        self.assertEqual(losable({"plain"}), ["plain"])


if __name__ == "__main__":
    unittest.main()
