"""The upkeep a screen quotes for a running concern is the upkeep the ledger charges: one function behind both
(Complaint 640: the rule is called on a stand-in that holds only what `upkeep` reads)."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.economy_production import ProductionMixin


class _Household:
    """Only what `upkeep` and `upkeep_by_concern` read; each concern's quote is a figure set here."""
    upkeep = ProductionMixin.upkeep
    upkeep_by_concern = ProductionMixin.upkeep_by_concern

    def __init__(self, quotes, operating, practice=()):
        self._quotes, self._practice = dict(quotes), set(practice)
        self.state = types.SimpleNamespace(projects=types.SimpleNamespace(operating=set(operating)))

    def _practice_set(self):
        return self._practice

    def _revenue_upkeep_candidates(self):
        return sorted(self._quotes)

    def venture_real_upkeep(self, node_id, units=None):
        return self._quotes[node_id]


class UpkeepQuoteMatchesLedger(unittest.TestCase):

    def test_ledger_upkeep_is_the_sum_of_quoted_upkeeps_of_the_running_concerns(self):
        household = _Household({"inn": 12.5, "mill": 40.25, "forge": 7.0}, operating={"inn", "mill", "forge"})
        quoted = sum(household.venture_real_upkeep(node_id) for node_id in ("inn", "mill", "forge"))
        self.assertAlmostEqual(household.upkeep(), quoted, places=6)

    def test_a_concern_that_is_not_open_is_not_charged(self):
        household = _Household({"inn": 12.5, "mill": 40.25}, operating={"inn"})
        self.assertEqual(household.upkeep_by_concern(), {"inn": 12.5})
        self.assertEqual(household.upkeep(), 12.5)

    def test_the_practice_the_founder_runs_is_charged_without_being_opened(self):
        household = _Household({"inn": 12.5, "craft": 3.0}, operating={"inn"}, practice={"craft"})
        self.assertEqual(household.upkeep(), 15.5)


if __name__ == "__main__":
    unittest.main()
