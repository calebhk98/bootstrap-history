"""Complaint 972: the repository's own mods directory yields the same catalogue object as naming none, in either call
order, so a solve over it is stopped at the same tolerance whichever caller reached it first."""
QUICK_TOPIC = True
import os
import unittest

from sim.prices import prices

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPOSITORY_MODS = os.path.join(ROOT, "mods")


class DefaultProductionEntriesIdentityTests(unittest.TestCase):

    def setUp(self):
        prices.reset_caches_for_tests()
        self.addCleanup(prices.reset_caches_for_tests)

    def test_the_named_repository_directory_first_is_the_default_object(self):
        named = prices.default_production_entries(REPOSITORY_MODS)
        self.assertIs(named, prices._DEFAULT_PRODUCTION_ENTRIES)
        self.assertIs(prices.default_production_entries(None), named)

    def test_naming_none_first_is_the_default_object(self):
        unnamed = prices.default_production_entries(None)
        self.assertIs(prices.default_production_entries(REPOSITORY_MODS), unnamed)
        self.assertIs(unnamed, prices._DEFAULT_PRODUCTION_ENTRIES)


if __name__ == "__main__":
    unittest.main()
