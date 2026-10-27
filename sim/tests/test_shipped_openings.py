"""A cache miss reads an entry shipped with the checkout under the same key before computing; a key with no
shipped entry is computed as before."""
QUICK_TOPIC = True

import json
import os
import tempfile
import unittest
from unittest import mock

from sim.prices import solve_cache

from sim.engine import shipped_openings, shipped_openings_build
from sim.markets import port_year
class ShippedEntryTests(unittest.TestCase):
    def setUp(self):
        self._shipped = tempfile.TemporaryDirectory()
        self._cache = tempfile.TemporaryDirectory()
        patcher = mock.patch.object(shipped_openings, "SHIPPED_OPENINGS_DIRECTORY", self._shipped.name)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._shipped.cleanup)
        self.addCleanup(self._cache.cleanup)
        self.cache = os.path.join(self._cache.name, "price_solves")

    def test_a_written_entry_reads_back_as_the_cache_would_return_it(self):
        value = {"producers": {"b": 0.1, "a": [1.5e-300, 3]}, "year": 0}
        shipped_openings.write("price_solves", "k1", value)
        self.assertEqual(shipped_openings.read("price_solves", "k1"), json.loads(json.dumps(value)))
        self.assertIsNone(shipped_openings.read("price_solves", "other"))
        self.assertEqual(shipped_openings.shipped_entries(), [("price_solves", "k1")])

    def test_a_miss_takes_the_shipped_entry_and_a_missing_one_is_computed(self):
        shipped_openings.write("price_solves", "k1", {"shipped": True})
        computed = []
        shipped = solve_cache.cached_json("k1", lambda: computed.append(1) or {"computed": True}, self.cache)
        own = solve_cache.cached_json("k2", lambda: computed.append(2) or {"computed": True}, self.cache)
        self.assertEqual(shipped, {"shipped": True})
        self.assertEqual(own, {"computed": True})
        self.assertEqual(computed, [2])

    def test_a_shipped_entry_in_another_cache_is_not_read(self):
        shipped_openings.write("agent_economy", "k1", {"shipped": True})
        self.assertEqual(solve_cache.cached_json("k1", lambda: {"computed": True}, self.cache), {"computed": True})

    def test_recording_names_each_entry_asked_for(self):
        with solve_cache.recording() as touched:
            solve_cache.cached_json("k3", lambda: 1, self.cache)
            solve_cache.cached_json("k3", lambda: 1, self.cache)
        self.assertEqual(touched, [(self.cache, "k3"), (self.cache, "k3")])

    def test_a_shortened_spin_up_is_never_shipped(self):
        with mock.patch.dict(os.environ, {port_year.SPIN_UP_YEARS_ENV: "3,2"}):
            with self.assertRaises(SystemExit):
                shipped_openings_build.build("rome_100ad")


if __name__ == "__main__":
    unittest.main()
