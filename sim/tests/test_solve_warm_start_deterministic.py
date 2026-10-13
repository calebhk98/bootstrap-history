"""An in-game price solve at a rate away from the starting one starts from the same solve at the starting
rate, so its answer depends on its own inputs only: the same whatever solves ran before it, and the same
from a cold disk cache as from a warm one."""
import shutil
import tempfile
import unittest

from sim.engine import prices as engine_prices, solve_cache

DOCUMENT = {"wage_rates_denarii_per_hour": {"labourer": {"rate": 2.0}}, "money_per_labour_hour": 2.0}


class WarmStartTests(unittest.TestCase):
    def setUp(self):
        self.original_directory = solve_cache.DEFAULT_CACHE_DIRECTORY
        self.directories = []

    def tearDown(self):
        solve_cache.DEFAULT_CACHE_DIRECTORY = self.original_directory
        for directory in self.directories:
            shutil.rmtree(directory, ignore_errors=True)
        engine_prices.reset_caches_for_tests()

    def _fresh(self):
        directory = tempfile.mkdtemp(prefix="warm_start_cache_")
        self.directories.append(directory)
        solve_cache.DEFAULT_CACHE_DIRECTORY = directory
        engine_prices.reset_caches_for_tests()

    def test_a_solve_does_not_depend_on_the_solves_before_it(self):
        starting = engine_prices.solve_prices.load_starting_interest_rate("rome_100ad")
        target = starting + 4 * engine_prices.INTEREST_RATE_BAND
        self._fresh()
        alone = engine_prices.solved_prices([], DOCUMENT, civilization_id="rome_100ad", interest_rate=target)
        self._fresh()
        engine_prices.solved_prices([], DOCUMENT, civilization_id="rome_100ad",
                                    interest_rate=starting + 9 * engine_prices.INTEREST_RATE_BAND)
        after_another = engine_prices.solved_prices([], DOCUMENT, civilization_id="rome_100ad", interest_rate=target)
        self.assertEqual(alone.prices_in_labour_hours, after_another.prices_in_labour_hours)


if __name__ == "__main__":
    unittest.main()
