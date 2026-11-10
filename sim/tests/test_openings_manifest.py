"""`openings_manifest`: a civilisation's shipped opening is stale unless the manifest holds the digest of the code now."""
QUICK_TOPIC = True

import os
import tempfile
import unittest

from sim.ui import openings_manifest


class StaleTest(unittest.TestCase):
    def test_missing_manifest_makes_every_civilisation_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "manifest.json")
            self.assertEqual(openings_manifest.stale_civs(["rome", "norse"], lambda: "now", path), ["rome", "norse"])

    def test_only_civilisations_built_from_another_digest_are_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "manifest.json")
            openings_manifest.record(["rome", "norse"], "before", path)
            openings_manifest.record(["rome"], "now", path)
            self.assertEqual(openings_manifest.read_manifest(path), {"norse": "before", "rome": "now"})
            self.assertEqual(openings_manifest.stale_civs(["rome", "norse", "mexica"], lambda: "now", path), ["norse", "mexica"])


if __name__ == "__main__":
    unittest.main()
