"""Node capital, upkeep and revenue are authored in labour hours: no branch file states them as a number of coins. The conversion of
those hours into a coin is test_coin_scale_rules."""
import glob
import json
import os
import unittest

from sim.engine import data

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


if __name__ == "__main__":
    unittest.main()
