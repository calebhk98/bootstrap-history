"""The installed mods' order is read and checked once while no mod file changes (load_civ asks for it on every
call, and a game year calls load_civ thousands of times)."""

QUICK_TOPIC = True

import os
import shutil
import tempfile
import time
import unittest
from unittest import mock

from sim.content import mods


def write_mod(directory, mod_id):
    os.makedirs(os.path.join(directory, mod_id))
    with open(os.path.join(directory, mod_id, "mod.json"), "w") as handle:
        handle.write('{"id": "%s", "name": "%s", "version": "1.0.0", "dependencies": [], "conflicts": []}' % (mod_id, mod_id))


class ModsOrderMemoTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        write_mod(self.directory, "test_first_a1b2")

    def tearDown(self):
        shutil.rmtree(self.directory)

    def test_unchanged_mods_are_read_once(self):
        with mock.patch.object(mods, "_ordered_mods", wraps=mods._ordered_mods) as reader:
            first = mods.get_ordered_mods(self.directory)
            second = mods.get_ordered_mods(self.directory)
        self.assertEqual(reader.call_count, 1)
        self.assertEqual([manifest.id for manifest in first], [manifest.id for manifest in second])

    def test_a_new_mod_is_seen(self):
        mods.get_ordered_mods(self.directory)
        write_mod(self.directory, "test_second_c3d4")
        self.assertEqual(sorted(manifest.id for manifest in mods.get_ordered_mods(self.directory)), ["test_first_a1b2", "test_second_c3d4"])

    def test_an_edited_mod_is_read_again(self):
        mods.get_ordered_mods(self.directory)
        path = os.path.join(self.directory, "test_first_a1b2", "mod.json")
        with open(path, "w") as handle:
            handle.write('{"id": "test_first_a1b2", "name": "renamed", "version": "1.0.0", "dependencies": [], "conflicts": []}')
        later = time.time() + 5
        os.utime(path, (later, later))
        self.assertEqual(mods.get_ordered_mods(self.directory)[0].name, "renamed")

    def test_the_caller_cannot_change_the_kept_order(self):
        mods.get_ordered_mods(self.directory).clear()
        self.assertEqual(len(mods.get_ordered_mods(self.directory)), 1)


if __name__ == "__main__":
    unittest.main()
