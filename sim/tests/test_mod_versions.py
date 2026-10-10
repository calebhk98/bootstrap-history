"""Mod manifests may require a minimum game version and a version range on a dependency."""

QUICK_TOPIC = True

import json
import subprocess
import sys
import unittest

from sim.engine.mods import ModError
from sim.game_version import GAME_VERSION, parse_version, satisfies
from sim.tests.test_mod_removal_and_civs import ModTestBase


class VersionTests(unittest.TestCase):
    def test_parse_pads_missing_parts(self):
        self.assertEqual(parse_version("1.2"), (1, 2, 0))
        self.assertEqual(parse_version("3"), (3, 0, 0))

    def test_parse_rejects_text(self):
        with self.assertRaises(ValueError):
            parse_version("one")

    def test_numbers_compare_not_strings(self):
        self.assertTrue(satisfies("1.10.0", ">=1.9"))

    def test_range_is_every_clause(self):
        self.assertTrue(satisfies("1.5.0", ">=1.2,<2"))
        self.assertFalse(satisfies("2.0.0", ">=1.2,<2"))

    def test_game_version_is_a_version(self):
        parse_version(GAME_VERSION)


class ManifestVersionTests(ModTestBase):
    def edit(self, mod_id, **changes):
        path = self.mods_dir / mod_id / "mod.json"
        manifest = json.loads(path.read_text())
        manifest.update(changes)
        path.write_text(json.dumps(manifest))

    def test_newer_game_required_is_refused(self):
        self.add_mod("test_acme_k3f9")
        self.edit("test_acme_k3f9", min_game_version="999.0.0")
        with self.assertRaises(ModError) as caught:
            self.manifests()
        self.assertIn("999.0.0", str(caught.exception))
        self.assertIn(GAME_VERSION, str(caught.exception))

    def test_current_game_is_enough(self):
        self.add_mod("test_acme_k3f9")
        self.edit("test_acme_k3f9", min_game_version=GAME_VERSION)
        self.assertEqual(len(self.manifests()), 1)

    def test_bad_min_version_is_refused(self):
        self.add_mod("test_acme_k3f9")
        self.edit("test_acme_k3f9", min_game_version="soon")
        with self.assertRaises(ModError):
            self.manifests()

    def test_dependency_range_met(self):
        self.add_mod("test_base_k3f9")
        self.edit("test_base_k3f9", version="1.4.0")
        self.add_mod("test_user_k3f9", dependencies=["test_base_k3f9>=1.2,<2"])
        found = {item.id: item for item in self.manifests()}
        self.assertEqual(found["test_user_k3f9"].dependencies, ["test_base_k3f9"])

    def test_dependency_range_unmet_names_both(self):
        self.add_mod("test_base_k3f9")
        self.edit("test_base_k3f9", version="2.0.0")
        self.add_mod("test_user_k3f9", dependencies=["test_base_k3f9>=1.2,<2"])
        with self.assertRaises(ModError) as caught:
            self.manifests()
        message = str(caught.exception)
        self.assertIn("test_user_k3f9", message)
        self.assertIn("test_base_k3f9", message)
        self.assertIn("2.0.0", message)

    def test_missing_dependency_with_range_is_still_missing(self):
        self.add_mod("test_user_k3f9", dependencies=["test_gone_k3f9>=1"])
        with self.assertRaises(ModError) as caught:
            self.manifests()
        self.assertIn("test_gone_k3f9", str(caught.exception))

    def test_command_line_prints_the_version(self):
        out = subprocess.run([sys.executable, "sim/simulator.py", "--version"],
                             capture_output=True, text=True, timeout=25)
        self.assertIn(GAME_VERSION, out.stdout + out.stderr)


if __name__ == "__main__":
    unittest.main()
