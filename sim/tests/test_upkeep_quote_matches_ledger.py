"""The upkeep a screen quotes for a running concern is the upkeep the ledger charges: one function behind both
(Complaint 640: the rule is called on a stand-in that holds only what `upkeep` reads)."""
QUICK_TOPIC = True

import types
import unittest

from sim.tests import production_host
from sim.tests.ui_stand_in import Game


def _Household(quotes, operating, practice=()):
    """The production module over the concerns that are open, each concern's quote a figure set here."""
    quote = lambda node_id, units=None: quotes[node_id]
    module = production_host.build(operating=set(operating), venture_real_upkeep=quote)
    module._practice_set = lambda: set(practice)
    module._revenue_upkeep_candidates = lambda: sorted(quotes)
    module.venture_real_upkeep = quote
    return module


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
