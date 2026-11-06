"""`world_rates.spoilage_rates` and `service_life_years`: the base file's entries by good with each installed mod's applied."""
QUICK_TOPIC = True

import json
import os
import shutil
import tempfile
import unittest

from sim.content import world_rates

MOD = "test_rates_c3d4"


def write_json(path, document):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as handle:
        json.dump(document, handle)


class WorldRates(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.directory)
        self.mods = os.path.join(self.directory, "mods")
        self.spoilage = os.path.join(self.directory, "spoilage.json")
        self.lives = os.path.join(self.directory, "service_lives.json")
        write_json(self.spoilage, {"_doc": "x", "rates_per_year": {"milk_kg": {"rate": 300.0}, "wheat_kg": {"rate": 0.08}}})
        write_json(self.lives, {"_doc": "x", "years": {"plough": {"years": 10, "source": "s"}}})

    def a_mod(self, files):
        write_json(os.path.join(self.mods, MOD, "mod.json"),
                   {"id": MOD, "name": MOD, "version": "1.0.0", "dependencies": [], "conflicts": []})
        for relative, document in files.items():
            write_json(os.path.join(self.mods, MOD, "data", "world", relative), document)

    def test_without_mods_the_rates_are_the_base_files(self):
        self.assertEqual(world_rates.spoilage_rates(self.mods, self.spoilage), {"milk_kg": 300.0, "wheat_kg": 0.08})
        self.assertEqual(world_rates.service_life_years(self.mods, self.lives), {"plough": 10.0})

    def test_a_mod_adds_a_good_of_its_own_and_overrides_a_base_one(self):
        self.a_mod({"spoilage.json": {"rates_per_year": {MOD + ":fruit_kg": {"rate": 5.0},
                                                         "wheat_kg": {"override": True, "rate": 0.5}}},
                    "service_lives.json": {"years": {MOD + ":wagon": {"years": 30}}}})
        self.assertEqual(world_rates.spoilage_rates(self.mods, self.spoilage),
                         {"milk_kg": 300.0, "wheat_kg": 0.5, MOD + ":fruit_kg": 5.0})
        self.assertEqual(world_rates.service_life_years(self.mods, self.lives), {"plough": 10.0, MOD + ":wagon": 30.0})

    def test_a_mod_removes_a_base_good(self):
        self.a_mod({"spoilage.json": {"rates_per_year": {"milk_kg": {"remove": True}}}})
        self.assertEqual(world_rates.spoilage_rates(self.mods, self.spoilage), {"wheat_kg": 0.08})


if __name__ == "__main__":
    unittest.main()
