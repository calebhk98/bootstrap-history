"""Derived node figures follow the techniques held now, not only the ones a civilisation starts with (Complaints/317)."""
import unittest

from sim import simulator
from sim.engine import data, node_revenue, prices


class HeldTechniques(unittest.TestCase):

    def setUp(self):
        _tree, _document, self.nodes, _wages, _goods = simulator.load()
        self.civ = simulator.load_civ("rome_100ad")
        self.schedule = data.starting_schedule("rome_100ad")
        self.start = set(self.civ["starting_techs"])

    def derive(self, held):
        return node_revenue.for_civilisation(self.nodes, self.civ, self.schedule, held_techs=held)

    def test_a_second_held_set_is_derived_and_changes_some_figure(self):
        extra = sorted(prices.all_gate_nodes() - self.start)
        base = self.derive(self.start)
        node_revenue.derivation_calls.clear()
        later = self.derive(self.start | set(extra))
        self.assertEqual(len(node_revenue.derivation_calls), 1, "a changed gate set must re-derive")
        changed = [node_id for node_id in base if base[node_id].get("rev_hours") != later[node_id].get("rev_hours")]
        self.assertTrue(changed)

    def test_the_cache_is_keyed_on_held_gates_only(self):
        self.derive(self.start)
        node_revenue.derivation_calls.clear()
        self.derive(self.start | {"a_tech_that_gates_no_technique"})
        self.assertEqual(node_revenue.derivation_calls, [])

    def test_default_is_the_starting_techniques(self):
        explicit = self.derive(self.start)
        default = node_revenue.for_civilisation(self.nodes, self.civ, self.schedule)
        self.assertEqual({k: v.get("rev_hours") for k, v in explicit.items()},
                         {k: v.get("rev_hours") for k, v in default.items()})


if __name__ == "__main__":
    unittest.main()
