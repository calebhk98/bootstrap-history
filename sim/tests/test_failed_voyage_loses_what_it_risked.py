"""Complaint 133: a failed action takes the hull, the crew and the cargo it risked.

A node's `risks` is {"crew": {trade: share}, "hull": {material: share}, "cargo": {material: share}}.
Small fixtures only; nothing here builds a game."""

QUICK_TOPIC = True

import random
import unittest
from types import SimpleNamespace

from sim.engine import tree_merge, validate_action_results
from sim.engine.action_loss import ActionLossMixin
from sim.engine.society_hazards import HazardsMixin


class _Host(ActionLossMixin, HazardsMixin):

    def __init__(self, risks, employees=None, stock=None, seed=1):
        self.nodes = {"voyage": {"id": "voyage", "risks": risks} if risks is not None else {"id": "voyage"}}
        self.state = SimpleNamespace(household=SimpleNamespace(employees=dict(employees or {})))
        self.rng = random.Random(seed)
        self.stock = dict(stock or {})

    def stock_held(self, material):
        return self.stock.get(material, 0.0)

    def change_stock(self, material, units):
        self.stock[material] = self.stock.get(material, 0.0) + units


class FailedVoyageTests(unittest.TestCase):

    def test_a_node_that_risks_nothing_loses_nothing(self):
        host = _Host(None, employees={"sailor": 50.0}, stock={"timber_m3": 10.0})
        self.assertEqual(host.lose_what_was_risked("voyage"), [])
        self.assertEqual(host.state.household.employees, {"sailor": 50.0})
        self.assertEqual(host.stock, {"timber_m3": 10.0})

    def test_the_crew_loses_about_the_share_risked_and_the_loss_is_whole_people(self):
        host = _Host({"crew": {"sailor": 0.4}}, employees={"sailor": 1000.0, "carpenter": 20.0})
        host.lose_what_was_risked("voyage")
        left = host.state.household.employees["sailor"]
        self.assertEqual(left, int(left))
        self.assertTrue(540 < left < 660, left)
        self.assertEqual(host.state.household.employees["carpenter"], 20.0)

    def test_a_crew_lost_entirely_leaves_the_books(self):
        host = _Host({"crew": {"sailor": 1.0}}, employees={"sailor": 12.0})
        host.lose_what_was_risked("voyage")
        self.assertNotIn("sailor", host.state.household.employees)

    def test_hull_and_cargo_are_taken_from_the_held_stock_by_the_share_risked(self):
        host = _Host({"hull": {"timber_m3": 0.5}, "cargo": {"wine_common_kg": 0.25}},
                     stock={"timber_m3": 100.0, "wine_common_kg": 80.0, "iron_bar_kg": 7.0})
        lines = host.lose_what_was_risked("voyage")
        self.assertEqual(host.stock, {"timber_m3": 50.0, "wine_common_kg": 60.0, "iron_bar_kg": 7.0})
        self.assertEqual(len(lines), 2)
        self.assertTrue(any("hull" in line for line in lines))
        self.assertTrue(any("cargo" in line for line in lines))

    def test_stock_that_is_not_held_is_not_made_negative(self):
        host = _Host({"hull": {"timber_m3": 0.5}}, stock={})
        self.assertEqual(host.lose_what_was_risked("voyage"), [])
        self.assertEqual(host.stock.get("timber_m3", 0.0), 0.0)

    def test_the_same_seed_loses_the_same_people(self):
        first = _Host({"crew": {"sailor": 0.3}}, employees={"sailor": 200.0}, seed=7)
        second = _Host({"crew": {"sailor": 0.3}}, employees={"sailor": 200.0}, seed=7)
        first.lose_what_was_risked("voyage")
        second.lose_what_was_risked("voyage")
        self.assertEqual(first.state.household.employees, second.state.household.employees)


class AuthoredRisksTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.nodes = {node["id"]: node for node in tree_merge.build_tree().tree["nodes"]}

    def test_the_risks_are_well_formed(self):
        self.assertEqual(validate_action_results.check_risks(self.nodes), [])

    def test_the_ocean_voyages_risk_a_crew_a_hull_and_a_cargo(self):
        for node_id in ("exp_coastal_africa", "exp_africa_circumnavigation", "exp_atlantic_crossing"):
            risks = self.nodes[node_id].get("risks") or {}
            self.assertTrue(risks.get("crew") and risks.get("hull") and risks.get("cargo"), node_id)

    def test_a_risk_names_a_share_between_nothing_and_everything(self):
        bad = {"a": {"id": "a", "risks": {"crew": {"sailor": 1.5}, "hull": {"x": 0.0}, "gold": {"y": 0.1}}}}
        self.assertEqual(len(validate_action_results.check_risks(bad)), 3)


if __name__ == "__main__":
    unittest.main()
