"""The full-length opening topics refuse to compute a spin-up, trace or margin that is neither on disk nor shipped
(Complaints/464, 557): they raise StaleShippedOpening at once, naming the command that regenerates the openings."""
import json
import os
import tempfile
import unittest

from sim.engine import solve_cache
from sim.tests.full_length_opening_support import StaleShippedOpening, refusing_to_compute_openings

QUICK_TOPIC = True


class StaleOpeningGuardTests(unittest.TestCase):
    def test_a_missing_spin_up_raises_without_computing(self):
        computed = []
        with tempfile.TemporaryDirectory() as root, refusing_to_compute_openings():
            directory = os.path.join(root, "agent_economy")
            os.makedirs(directory)
            with self.assertRaises(StaleShippedOpening) as caught:
                solve_cache.cached_json("nokey", lambda: computed.append(1), cache_dir=directory)
        self.assertEqual(computed, [])
        self.assertIn("simulator.py openings", str(caught.exception))    # presentation: the message names the remedy

    def test_an_entry_on_disk_is_read_and_a_cheap_namespace_still_computes(self):
        with tempfile.TemporaryDirectory() as root, refusing_to_compute_openings():
            kept = os.path.join(root, "agent_economy")
            os.makedirs(kept)
            with open(os.path.join(kept, "key.json"), "w", encoding="utf-8") as handle:
                json.dump({"year": 3}, handle)
            self.assertEqual(solve_cache.cached_json("key", lambda: None, cache_dir=kept), {"year": 3})
            cheap = os.path.join(root, "price_solves")
            os.makedirs(cheap)
            self.assertEqual(solve_cache.cached_json("other", lambda: {"solved": True}, cache_dir=cheap), {"solved": True})

    def test_the_guard_is_lifted_afterwards(self):
        real = solve_cache.cached_json
        with refusing_to_compute_openings():
            self.assertIsNot(solve_cache.cached_json, real)
        self.assertIs(solve_cache.cached_json, real)


if __name__ == "__main__":
    unittest.main()
