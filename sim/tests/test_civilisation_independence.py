"""Complaints/131 and 132: the game runs with any civilisation file absent. The default is the preferred civilisation
or, if its file is absent, the first one present; nothing else names it. The source scans that no engine code names a
civilisation are in test_civilisation_independence_scans.

Unittest style so importing it does not pull in the engine.
"""
QUICK_TOPIC = True

import unittest
from unittest import mock

from sim import default_civilisation
from sim.default_civilisation import PREFERRED_DEFAULT_CIVILISATION

# the function without its cache, so each case reads the files it is given
default_civilisation_id = default_civilisation.default_civilisation_id.__wrapped__


def with_files(file_ids):
    return mock.patch.object(default_civilisation, "_file_ids", return_value=file_ids)


class DefaultCivilisation(unittest.TestCase):

    def test_the_preferred_civilisation_is_the_default_when_its_file_is_present(self):
        with with_files(["a_first", PREFERRED_DEFAULT_CIVILISATION, "z_last"]):
            self.assertEqual(default_civilisation_id(), PREFERRED_DEFAULT_CIVILISATION)

    def test_the_first_civilisation_present_is_the_default_when_the_preferred_file_is_absent(self):
        with with_files(["b_second", "a_first"]):
            self.assertEqual(default_civilisation_id(), "b_second")

    def test_with_no_civilisation_file_at_all_the_preferred_name_is_still_answered(self):
        with with_files([]):
            self.assertEqual(default_civilisation_id(), PREFERRED_DEFAULT_CIVILISATION)

    def test_the_files_listed_are_sorted_json_files_without_the_reference_data(self):
        with mock.patch.object(default_civilisation.os, "listdir",
                               return_value=["rome.json", "_TECH_EFFECTS.json", "han.json", "notes.txt"]):
            self.assertEqual(default_civilisation._file_ids(), ["han", "rome"])

    def test_every_civilisation_file_loads_without_the_preferred_one(self):
        from sim.engine import data
        ids = default_civilisation._file_ids()
        self.assertTrue(ids)
        for civilisation_id in ids:
            self.assertEqual(data.load_civ(civilisation_id)["id"], civilisation_id)


if __name__ == "__main__":
    unittest.main()
