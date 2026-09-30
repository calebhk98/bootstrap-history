"""The upkeep a screen quotes for a running concern is the upkeep the ledger
charges: one function behind both."""
import unittest

from .harness import *  # noqa: F401,F403


def _han_with_running_concerns():
    household = sim(civ="han_china_100ad", capital=1e9)
    node_ids = [node_id for node_id in NODES
                if NODES[node_id]["up"] > 0 and household.is_venture(node_id)][:4]
    for node_id in node_ids:
        household.done.add(node_id)
        household.operating.add(node_id)
    household._done_changed()
    return household, node_ids


class UpkeepQuoteMatchesLedger(unittest.TestCase):

    def test_ledger_upkeep_is_the_sum_of_quoted_upkeeps(self):
        household, node_ids = _han_with_running_concerns()
        self.assertNotEqual(household.price_index, 1.0)
        running = [node_id for node_id in node_ids if household.running(node_id)]
        self.assertTrue(running)
        quoted = sum(household.venture_real_upkeep(node_id) for node_id in running)
        self.assertAlmostEqual(household.upkeep(), quoted, places=6)
