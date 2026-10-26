"""Reading the deposits of several resources in turn keeps each resource's base rows (no recomputation per switch)."""
QUICK_TOPIC = True

import unittest

from sim.tests import resources_stand_in


class DepositBaseCacheTests(unittest.TestCase):
    def test_alternating_resources_reuse_their_rows(self):
        host = resources_stand_in.build()
        names = [name for name in ("iron", "lead", "copper", "silver") if host.mine_resource_id(name)][:2]
        if len(names) < 2:
            self.skipTest("fewer than two mined resources")
        first = host.deposit_base(names[0])
        second = host.deposit_base(names[1])
        self.assertIs(host.deposit_base(names[0]), first)
        self.assertIs(host.deposit_base(names[1]), second)


if __name__ == "__main__":
    unittest.main()
