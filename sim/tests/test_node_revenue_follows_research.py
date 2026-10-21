"""A technique the society learns that gates production changes the derived figures of the nodes that use it
(Complaints/317): the derivation is cached per held gate set, so it runs once for a new set and not again for a
technique that gates nothing. Called on the tree and civilisation directly; the saved game is in
test_node_revenue_follows_research_scenario."""
import unittest

from sim.engine import data, money_units, node_revenue, prices
from sim.engine.node_rederive import held_gate_set
from sim.engine.wage_schedule import build_schedule

CIVILISATION = "rome_100ad"


def derive(held):
    _tree, _document, nodes, _wages, _goods = data.load(civilization_id=CIVILISATION)
    civ = data.load_civ(CIVILISATION)
    schedule = build_schedule(data.TRADE_REGISTRY, civ)
    return node_revenue.for_civilisation(nodes, civ, schedule, held_techs=held), schedule


def hours(derived):
    return {node_id: node.get("rev_hours") for node_id, node in derived.items()}


class RederivesOnResearch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        civ = data.load_civ(CIVILISATION)
        cls.start = set(civ["starting_techs"])
        cls.learned = sorted(prices.all_gate_nodes() - cls.start)
        cls.before, _schedule = derive(cls.start)
        node_revenue.derivation_calls.clear()
        cls.after, cls.schedule = derive(cls.start | set(cls.learned))
        cls.derivations = len(node_revenue.derivation_calls)

    def test_a_new_gate_set_derives_once_and_moves_a_dependent_figure(self):
        self.assertLessEqual(self.derivations, 1)
        self.assertTrue([node_id for node_id in hours(self.before) if hours(self.before)[node_id] != hours(self.after)[node_id]])

    def test_money_fields_follow_the_hours(self):
        rate = self.schedule.money_per_labour_hour
        money_units.price_nodes(self.after.values(), self.schedule.wages_per_hour(), rate)
        for node_id, node in self.after.items():
            self.assertAlmostEqual(node["rev"], node["rev_hours"] * rate, delta=1e-6 * max(1.0, node["rev"]), msg=node_id)

    def test_a_technique_that_gates_nothing_leaves_the_gate_set_and_derives_nothing(self):
        held = self.start | set(self.learned) | {"a_tech_that_gates_no_technique"}
        self.assertEqual(held_gate_set(held), held_gate_set(self.start | set(self.learned)))
        node_revenue.derivation_calls.clear()
        again, _schedule = derive(held)
        self.assertEqual(node_revenue.derivation_calls, [])
        self.assertEqual(hours(again), hours(self.after))

    def test_a_gate_the_society_learns_enters_the_gate_set(self):
        self.assertTrue(set(self.learned) <= held_gate_set(self.start | set(self.learned)))
        self.assertFalse(set(self.learned) & held_gate_set(self.start))


if __name__ == "__main__":
    unittest.main()
