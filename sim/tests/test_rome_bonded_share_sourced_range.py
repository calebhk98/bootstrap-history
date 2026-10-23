"""Rome's declared bonded share sits inside the range its own source note gives (Scheidel 2005, JRS 95: 64-79). The range is
read from the civilisation file's note, never typed here. Pure data: no game is built. The share after played years is
Complaints/648 (measured by the command named there)."""
import json
import os
import re
import unittest

from sim.tests.harness import ROOT

QUICK_TOPIC = True


def _civ():
    with open(os.path.join(ROOT, "data", "civilizations", "rome_100ad.json")) as handle:
        return json.load(handle)


def sourced_range(civ):
    """(low, high) as shares, read from the 'range being 8 to 15 per cent' note in the civilisation's cast source."""
    found = re.search(r"range being (\d+(?:\.\d+)?) to (\d+(?:\.\d+)?) per cent", civ["_internal"]["cast"]["source"])
    if not found:
        raise AssertionError("rome_100ad's cast source no longer states a range in per cent: nothing to read")
    return float(found.group(1)) / 100.0, float(found.group(2)) / 100.0


class DeclaredBondedShareAgreesWithItsSource(unittest.TestCase):

    def test_the_note_states_a_range_with_low_under_high(self):
        low, high = sourced_range(_civ())
        self.assertTrue(0.0 < low < high < 1.0, (low, high))

    def test_the_declared_bonded_share_is_inside_the_sourced_range(self):
        civ = _civ()
        low, high = sourced_range(civ)
        bonded = [entry for entry in civ["cast"]["strata"] if entry.get("bonded")]
        self.assertEqual(len(bonded), 1)
        self.assertTrue(low <= bonded[0]["share"] <= high, (low, bonded[0]["share"], high))


if __name__ == "__main__":
    unittest.main()
