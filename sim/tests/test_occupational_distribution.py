"""The occupation-group data (Complaint 619, DESIGN 4.2): every registry trade is in exactly one group and every band cites a source
(data/world/occupation_groups.json). Reads data only. The baseline's shares against these bands are measured with
`python3 sim/simulator.py economy-check --civs rome_100ad --years 1 --occupations`."""

import collections
import json
import os
import unittest

from sim.engine.ui_port import ROOT
from sim.labour.api import occupation_groups

QUICK_TOPIC = True


class GroupData(unittest.TestCase):
    def test_every_registry_trade_is_in_exactly_one_group(self):
        with open(os.path.join(ROOT, "data", "world", "trades.json"), encoding="utf-8") as handle:
            registry = set(json.load(handle)["trades"])
        counted = collections.Counter(trade for group in occupation_groups()["groups"].values() for trade in group["trades"])
        self.assertEqual(set(counted), registry)
        self.assertEqual([trade for trade, times in counted.items() if times > 1], [])

    def test_every_band_cites_a_source_or_is_the_unattributed_cap(self):
        data = occupation_groups()
        for group_id, group in data["groups"].items():
            low, high = group["band"]
            self.assertLessEqual(low, high)
            for source in group["sources"]:
                self.assertIn(source, data["sources"])
            if group_id != "unattributed":
                self.assertTrue(group["sources"], group_id)


if __name__ == "__main__":
    unittest.main()
