"""allowed_entries: a society that holds no capability is offered no entry that requires one."""

QUICK_TOPIC = True

import unittest

from sim.engine.economy_port_setup import allowed_entries
from sim.world import demand

PRODUCTION = demand.production_data()


class AllowedWithoutDraught(unittest.TestCase):

    def test_with_nothing_held_no_allowed_entry_requires_a_node(self):
        allowed = allowed_entries(PRODUCTION, set())
        self.assertIn("wheat_hoe_kg", allowed)
        self.assertEqual(sorted(key for key in allowed if PRODUCTION[key].get("requires_node")), [])


if __name__ == "__main__":
    unittest.main()
