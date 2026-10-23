"""Complaint 190: things a very rich founder can spend on.

Endowments, public works, patronage and display, commerce and finance, grants to the state and expeditions are ordinary
works declared in data (data/branches/56_benefactions.json). Each acts only through mechanics channels the engine already
reads (data/branches/MECHANICS.md), costs from its labour and materials, and keeps costing upkeep for as long as it is
open. This file validates what the branch declares, in the tree as built; that the engine moves the
channels they declare is test_effect_channels."""
QUICK_TOPIC = True

import json
import os
import unittest

from sim.tests.harness import NODES, ROOT

with open(os.path.join(ROOT, "data", "branches", "56_benefactions.json")) as _branch:
    WORKS = tuple(node["id"] for node in json.load(_branch))
PRESENT = [work for work in WORKS if work in NODES]
# a work with a yearly programme is kept up; one without is paid for once (a transfer, a charter) and is knowledge after
KEPT = [work for work in PRESENT if NODES[work]["up"] > 0]
ONCE = [work for work in PRESENT if work not in KEPT]
MAINTENANCE_SHARE_OF_BUILD = 0.02
# the keys of a work's mechanics that move something an engine reading can measure
MEASURABLE_CHANNELS = {"schooling_flow", "standing", "hazard_counters", "reach", "supervision_room", "protection",
                       "patron_protection", "credit_line"}


def is_concern_node(node):
    """The engine's test (Sim.is_concern_node) of a going concern: it earns or costs to keep up."""
    return node["rev"] > 0 or node["up"] > 0


class DeclaredWorksTests(unittest.TestCase):
    def test_every_work_declared_in_the_benefactions_branch_reaches_the_tree_and_there_is_at_least_one(self):
        self.assertTrue(WORKS)
        self.assertEqual(sorted(set(WORKS) - set(PRESENT)), [])

    def test_some_works_are_paid_once_and_the_rest_are_kept_up(self):
        self.assertTrue(ONCE)
        self.assertTrue(KEPT)

    def test_a_work_with_a_yearly_programme_is_a_going_concern_and_one_without_is_not(self):
        for work in KEPT:
            self.assertTrue(is_concern_node(NODES[work]), work)
        for work in ONCE:
            self.assertFalse(is_concern_node(NODES[work]), work)


class PaidOnceTests(unittest.TestCase):
    def test_earns_nothing_and_costs_nothing_to_keep(self):
        for work in ONCE:
            self.assertEqual((NODES[work]["rev"], NODES[work]["up"]), (0, 0), work)

    def test_costs_labour_to_bring_about(self):
        for work in ONCE:
            self.assertGreater(NODES[work]["_labour_cost"], 0, work)

    def test_declares_mechanics(self):
        for work in ONCE:
            self.assertTrue(NODES[work].get("mechanics"), work)


class KeptUpTests(unittest.TestCase):
    def test_earns_nothing_of_its_own(self):
        for work in KEPT:
            self.assertEqual(NODES[work]["rev"], 0, work)

    def test_is_built_from_labour_and_materials_not_a_typed_capital_figure(self):
        for work in KEPT:
            self.assertGreater(NODES[work]["_labour_cost"], 0, work)
            self.assertGreater(NODES[work]["_material_cost"], 0, work)

    def test_costs_upkeep_at_least_a_maintenance_share_of_its_build(self):
        for work in KEPT:
            node = NODES[work]
            self.assertGreaterEqual(node["up"], MAINTENANCE_SHARE_OF_BUILD * (node["_labour_cost"] + node["_material_cost"]) * 0.99, work)

    def test_declares_mechanics_including_a_kept_institution(self):
        for work in KEPT:
            mechanics = NODES[work].get("mechanics")
            self.assertTrue(mechanics, work)
            self.assertIn("capability", mechanics, work)

    def test_declares_at_least_one_effect_channel_the_engine_reads(self):
        for work in KEPT:
            mechanics = NODES[work]["mechanics"]
            measurable = [channel for channel in mechanics if channel in MEASURABLE_CHANNELS] \
                + (["staff_capacity"] if (mechanics.get("staff_capacity") or {}).get("scholars") else [])
            self.assertTrue(measurable, (work, sorted(mechanics)))


if __name__ == "__main__":
    unittest.main()
