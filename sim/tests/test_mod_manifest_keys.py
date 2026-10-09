"""A mod manifest must carry the keys the loader reads; any other key (author, credits, a description) is the author's own metadata and loads."""

QUICK_TOPIC = True

import json
import unittest

from sim.engine.mods import ModError
from sim.engine.mods_base import MANIFEST_KEYS
from sim.tests.test_mod_removal_and_civs import ModTestBase


class ManifestKeyTests(ModTestBase):
    def add_with_extra_keys(self, **extra):
        self.add_mod("test_acme_k3f9")
        path = self.mods_dir / "test_acme_k3f9" / "mod.json"
        manifest = json.loads(path.read_text())
        manifest.update(extra)
        path.write_text(json.dumps(manifest))

    def test_extra_metadata_keys_load(self):
        self.add_with_extra_keys(author="Bob", coauthors=["Ann"], description="A mod.")
        self.assertEqual([found.id for found in self.manifests()], ["test_acme_k3f9"])

    def test_missing_key_is_refused(self):
        self.add_mod("test_acme_k3f9")
        path = self.mods_dir / "test_acme_k3f9" / "mod.json"
        manifest = json.loads(path.read_text())
        del manifest["conflicts"]
        path.write_text(json.dumps(manifest))
        with self.assertRaises(ModError) as caught:
            self.manifests()
        self.assertIn("conflicts", str(caught.exception))

    def test_known_keys_come_from_the_manifest_type(self):
        self.assertEqual(set(MANIFEST_KEYS),
                         {"id", "name", "version", "dependencies", "conflicts"})

    def test_plain_manifest_still_loads(self):
        self.add_mod("test_acme_k3f9")
        self.assertEqual([found.id for found in self.manifests()], ["test_acme_k3f9"])


if __name__ == "__main__":
    unittest.main()
