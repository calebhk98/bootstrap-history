"""Which built nodes a loss event may take (Complaints 259): not inherited, not a measured goal (a measurement cannot be
forgotten, so it is never announced twice), and by default not a dispersed corpus."""
import unittest
from types import SimpleNamespace

from sim.tests.ui_stand_in import FactViews
from sim.engine.forward_mechanics import ForwardMechanicsMixin

QUICK_TOPIC = True


class Host(ForwardMechanicsMixin, FactViews):
    def __init__(self, done, granted=(), dispersed=()):
        self.nodes = {"plain": {}, "inherited": {}, "goal": {"win_condition": True}, "copies": {}, "other": {}}
        self.state = SimpleNamespace(projects=SimpleNamespace(done=set(done), granted=set(granted)))
        self._dispersed = set(dispersed)

    def corpus_is_dispersed(self, node_id):
        return node_id in self._dispersed


EVERYTHING = {"plain", "inherited", "goal", "copies", "other"}


class LosableNodes(unittest.TestCase):

    def test_a_measured_goal_is_never_losable(self):
        self.assertNotIn("goal", Host(EVERYTHING).losable_node_ids())

    def test_an_inherited_node_is_never_losable(self):
        self.assertNotIn("inherited", Host(EVERYTHING, granted={"inherited"}).losable_node_ids())

    def test_a_dispersed_corpus_is_kept_by_default_and_losable_when_asked(self):
        host = Host(EVERYTHING, dispersed={"copies"})
        self.assertNotIn("copies", host.losable_node_ids())
        self.assertIn("copies", host.losable_node_ids(keep_dispersed=False))

    def test_what_is_left_is_every_other_built_node_in_order(self):
        self.assertEqual(Host(EVERYTHING, granted={"inherited"}, dispersed={"copies"}).losable_node_ids(),
                         ["other", "plain"])

    def test_an_unbuilt_node_is_not_losable(self):
        self.assertEqual(Host({"plain"}).losable_node_ids(), ["plain"])


if __name__ == "__main__":
    unittest.main()
