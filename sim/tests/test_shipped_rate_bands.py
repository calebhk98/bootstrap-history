"""The opening's price solves are shipped for the other interest-rate bands under the keys a game computes,
and a shipped solve is the solve a game would compute. Which rates are banded is test_shipped_rate_band_range_rule."""
import os
import tempfile
import unittest
from unittest import mock

from sim.tests import harness  # noqa: F401  (shortens the spin-up for the suite)
from sim.engine import prices, shipped_openings, shipped_rate_bands, solve_cache
from sim.engine.data import calculated_goods_table, load_civ

CIVILISATION_ID = "rome_100ad"


def _table_at(civ, rate):
    return calculated_goods_table(frozenset(), civilization=civ, interest_rate=rate)


class ShippedBandTests(unittest.TestCase):
    def setUp(self):
        self.civ = load_civ(CIVILISATION_ID)
        self.starting_rate = float(self.civ["starting_interest_rate"])
        self.band = prices.band_interest_rate(self.starting_rate + prices.INTEREST_RATE_BAND, self.starting_rate)

    def _fresh_cache(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        cache = os.path.join(directory.name, "price_solves")
        patcher = mock.patch.object(solve_cache, "DEFAULT_CACHE_DIRECTORY", cache)
        patcher.start()
        self.addCleanup(patcher.stop)
        prices._SOLVE_CACHE.clear()
        self.addCleanup(prices._SOLVE_CACHE.clear)
        return cache

    def test_a_shipped_band_equals_the_solve_computed_cold(self):
        shipped = tempfile.TemporaryDirectory()
        self.addCleanup(shipped.cleanup)
        patcher = mock.patch.object(shipped_openings, "SHIPPED_OPENINGS_DIRECTORY", shipped.name)
        patcher.start()
        self.addCleanup(patcher.stop)
        cache = self._fresh_cache()
        with solve_cache.recording() as touched, shipped_rate_bands.SolveRecorder() as solves:
            _table_at(self.civ, self.starting_rate)
        starting_keys = list(dict.fromkeys(key for _directory, key in touched))
        with solve_cache.recording() as band_touched:
            shipped_rate_bands.solve_other_bands(solves.at_starting_rate(self.starting_rate), self.starting_rate, 2)
        band_keys = [key for _directory, key in dict.fromkeys(band_touched) if key not in starting_keys]
        self.assertTrue(band_keys)
        computed = _table_at(self.civ, self.band)
        for key in band_keys:
            shipped_openings.write("price_solves", key, solve_cache.cached_json(key, lambda: self.fail("missing"), cache))
        # A new disk cache and process memory: the band can now come only from the shipped entries.
        self._fresh_cache()
        with mock.patch.object(prices, "_solve_to_json", side_effect=AssertionError("solved the band")):
            from_shipped = _table_at(self.civ, self.band)
        self.assertEqual(from_shipped, computed)


if __name__ == "__main__":
    unittest.main()
