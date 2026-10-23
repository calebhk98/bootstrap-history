"""Rome holds none of the technologies that declare the `disease_burden` mechanic when the game starts, so the disease burden
wiring changes nothing on its unshocked baseline until one is completed. Read off the tree and the civilisation data, no game."""
QUICK_TOPIC = True
import unittest

from .harness import NODES, S


class RomeStartsWithoutDiseaseTechnologiesTests(unittest.TestCase):
    def test_the_tree_declares_disease_burden_nodes(self):
        self.assertTrue([node_id for node_id, node in NODES.items() if "disease_burden" in (node.get("mechanics") or {})])

    def test_rome_starts_with_none_of_them(self):
        declaring = {node_id for node_id, node in NODES.items() if "disease_burden" in (node.get("mechanics") or {})}
        self.assertEqual(sorted(declaring & set(S.load_civ("rome_100ad")["starting_techs"])), [])


if __name__ == "__main__":
    unittest.main()
