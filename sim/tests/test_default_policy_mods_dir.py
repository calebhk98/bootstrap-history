"""The standing policy of a new seat includes the defaults of the policy switches the mods of the directory it is handed add
(Complaint 840: it read the process global, so a game over another directory got the wrong switches)."""
QUICK_TOPIC = True

import json
import os
import shutil
import tempfile
import unittest

from sim.engine.seat_defaults import default_policy

MOD = "acme_pulse_k3f9"
POLICY_COMMAND = {"commands": {MOD + ":pulse": {"kind": "policy", "summary": "s", "description": "d", "hook": "year_end", "default": False,
                                                "when": [{"path": "capital", "op": ">", "value": 1}], "do": [{"cmd": "status"}]}}}


def write_policy_mod(directory):
    os.makedirs(os.path.join(directory, MOD, "data", "ui"))
    with open(os.path.join(directory, MOD, "mod.json"), "w") as handle:
        json.dump({"id": MOD, "name": MOD, "version": "1.0.0", "dependencies": [], "conflicts": []}, handle)
    with open(os.path.join(directory, MOD, "data", "ui", "commands.json"), "w") as handle:
        json.dump(POLICY_COMMAND, handle)


class DefaultPolicyOfADirectory(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.directory)

    def test_a_mods_policy_switch_is_in_the_policy_of_the_directory_it_is_in(self):
        write_policy_mod(self.directory)
        self.assertIs(default_policy(False, self.directory)[MOD + ":pulse"], False)

    def test_the_switch_is_not_in_the_policy_of_a_directory_without_the_mod(self):
        write_policy_mod(self.directory)
        empty = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, empty)
        self.assertNotIn(MOD + ":pulse", default_policy(False, empty))


if __name__ == "__main__":
    unittest.main()
