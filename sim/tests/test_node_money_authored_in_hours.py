"""Node capital, upkeep and revenue are authored in labour hours; the money
fields a Sim reads are those hours in the civilisation's own coin."""
import glob
import json
import os
import unittest

from sim.engine import data, money_units
from sim.tests.test_money_units_one_boundary import BASE_CIVS, build

BRANCH_DIRECTORY = os.path.join(data.ROOT, "data", "branches")
AUTHORED_FIELDS = ("cap", "up", "rev")


def authored_nodes():
    for path in sorted(glob.glob(os.path.join(BRANCH_DIRECTORY, "[0-9]*.json"))):
        with open(path) as handle:
            yield from (node for node in json.load(handle) if isinstance(node, dict))


class NodeMoneyAuthoredInHours(unittest.TestCase):
    def test_branch_files_carry_hours_not_denarii(self):
        for node in authored_nodes():
            for field in AUTHORED_FIELDS:
                value = node.get(field)
                self.assertFalse(isinstance(value, (int, float)),
                                 "%s still authors %s as a number" % (node["id"], field))

    def test_sim_money_is_authored_hours_in_the_civilisations_coin(self):
        authored = {node["id"]: node for node in authored_nodes()}
        for civ in BASE_CIVS:
            sim = build(data.load_civ(civ))
            rate = sim.money_per_labour_hour()
            checked = 0
            for node_id, node in sim.nodes.items():
                if node_id not in authored:
                    continue
                for field in AUTHORED_FIELDS:
                    hours = authored[node_id].get(field + "_hours")
                    if hours is None:
                        continue
                    if field == "rev":
                        # revenue is re-derived against solved costs (sim/engine/node_revenue.py)
                        self.assertEqual(node["_rev_hours_authored"], hours)
                        hours = node["rev_hours"]
                    self.assertAlmostEqual(node[field], hours * rate,
                                           delta=1e-9 * (1 + hours * rate))
                    checked += 1
            self.assertGreater(checked, 1000)

    def test_engine_has_no_book_denarii_node_converter(self):
        self.assertFalse(hasattr(money_units, "NODE_MONEY_FIELDS"))
        self.assertFalse(hasattr(money_units, "book_to_hours"))


if __name__ == "__main__":
    unittest.main()
