"""`displacing_technique` with the category shares kept between calls names what the full scan of the tree named."""

QUICK_TOPIC = True

import random
import unittest

from sim.agents.group_jobs import category_mean_shares, displacing_technique, idle_share_of
from sim.tests.group_jobs_plain import displacing_technique_by_scanning

TRADES = ["smith", "farmer", "mason"]


class _Stratum:
    def __init__(self, plan):
        self.record = type("Record", (), {"plan": plan})()


class DisplacingTechniqueTests(unittest.TestCase):
    def test_written_out_tree(self):
        nodes = {
            "plough": {"cat": "farming", "lab": {"farmer": 1.0, "smith": 3.0}},
            "hoe": {"cat": "farming", "lab": {"farmer": 3.0, "smith": 1.0}},
            "idle": {"cat": "farming"},
            "anvil": {"cat": "metal", "lab": {"smith": 2.0}},
        }
        running = {"plough": 5, "hoe": 3, "anvil": 1}
        self.assertEqual(displacing_technique("smith", running, nodes), "hoe")
        self.assertEqual(displacing_technique("smith", running, nodes, category_mean_shares("smith", nodes)), "hoe")
        self.assertEqual(displacing_technique("mason", {"anvil": 1}, nodes), None)

    def test_random_trees_match_the_full_scan(self):
        for seed in range(60):
            generator = random.Random(seed)
            nodes = {}
            for number in range(generator.randint(0, 40)):
                labour = {trade: generator.choice([0.0, generator.random() * 10]) for trade in generator.sample(TRADES, generator.randint(0, 3))}
                node = {"cat": generator.choice(["a", "b", "c", None])}
                if generator.random() < 0.8:
                    node["lab"] = labour
                nodes["n%d" % number] = node
            running = {node_id: generator.randint(0, 5) for node_id in generator.sample(sorted(nodes), len(nodes) // 2)}
            running["absent"] = 2
            for trade in TRADES:
                expected = displacing_technique_by_scanning(trade, running, nodes)
                self.assertEqual(displacing_technique(trade, running, nodes), expected)
                self.assertEqual(displacing_technique(trade, running, nodes), expected)   # the kept shares, for the same tree
                self.assertEqual(displacing_technique(trade, running, nodes, category_mean_shares(trade, nodes)), expected)


class IdleShareTests(unittest.TestCase):
    def test_share_of_the_trades_hours(self):
        idle_hours = {"smith": (25.0, 100.0), "farmer": (0.0, 0.0)}
        self.assertEqual(idle_share_of(_Stratum({"trade": "smith"}), idle_hours), 0.25)
        self.assertIsNone(idle_share_of(_Stratum({"trade": "farmer"}), idle_hours))
        self.assertIsNone(idle_share_of(_Stratum({"trade": "mason"}), idle_hours))
        self.assertIsNone(idle_share_of(_Stratum({}), idle_hours))
