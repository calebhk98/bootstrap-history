"""A mod manifest with a key the loader does not read is refused."""

QUICK_TOPIC = True

import json
import unittest

from sim.engine.mods import ModError
from sim.engine.mods_base import MANIFEST_KEYS
from sim.tests.test_mod_removal_and_civs import ModTestBase


class ManifestKeyTests(ModTestBase):
    def add_with_extra_key(self, key):
        self.add_mod("test_acme_k3f9")
        path = self.mods_dir / "test_acme_k3f9" / "mod.json"
        manifest = json.loads(path.read_text())
        manifest[key] = "1.0"
        path.write_text(json.dumps(manifest))

    def test_unknown_key_is_refused_naming_key_and_known_keys(self):
        self.add_with_extra_key("min_game_version")
        with self.assertRaises(ModError) as caught:
            self.manifests()
        message = str(caught.exception)
        self.assertIn("min_game_version", message)
        for known in MANIFEST_KEYS:
            self.assertIn(known, message)

    def test_known_keys_come_from_the_manifest_type(self):
        self.assertEqual(set(MANIFEST_KEYS),
                         {"id", "name", "version", "dependencies", "conflicts"})

    def test_plain_manifest_still_loads(self):
        self.add_mod("test_acme_k3f9")
        self.assertEqual([found.id for found in self.manifests()], ["test_acme_k3f9"])


if __name__ == "__main__":
    unittest.main()
