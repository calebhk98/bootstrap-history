"""Reading the deposits of several resources in turn keeps each resource's base rows (no recomputation per switch)."""
QUICK_TOPIC = True

import json
import os
import types
import unittest

from sim.engine.mine_deposits import MineDepositsMixin
from sim.engine.state_holdings import HoldingsState
from sim.geography import api as geography

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class _Host(MineDepositsMixin):
    def __init__(self):
        self.world_map = geography.open_map()
        with open(os.path.join(ROOT, "data", "civilizations", "rome_100ad.json"), encoding="utf-8") as handle:
            self.civ = json.load(handle)
        self.holdings = HoldingsState()
        self.state = types.SimpleNamespace(holdings=self.holdings, scenario=types.SimpleNamespace(year=100))
        self.cfg = {"start_year": 100}

    def _capacity_naming(self, deposit_id):
        return 0.0


class DepositBaseCacheTests(unittest.TestCase):
    def test_alternating_resources_reuse_their_rows(self):
        host = _Host()
        names = [name for name in ("iron", "lead", "copper", "silver") if host.mine_resource_id(name)][:2]
        if len(names) < 2:
            self.skipTest("fewer than two mined resources")
        first = host._deposit_base(names[0])
        second = host._deposit_base(names[1])
        self.assertIs(host._deposit_base(names[0]), first)
        self.assertIs(host._deposit_base(names[1]), second)


if __name__ == "__main__":
    unittest.main()
