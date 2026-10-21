"""Complaints 239, 94 and 266: the map, education, demography and divergence screens are registered commands with
help, and their aliases reach them (Complaint 640: the registry, no game; the figures on each screen are
test_missing_screens_scenario)."""
import unittest

from sim.ui.proto import command_registry
from sim.ui.proto.typed import parse_typed

QUICK_TOPIC = True


class RegistryTests(unittest.TestCase):

    def test_each_screen_is_registered_with_help(self):
        for name in ("map", "education", "demography", "divergence"):
            self.assertTrue(name in command_registry.COMMANDS, name)
            entry = command_registry.COMMANDS[name]
            self.assertTrue(entry["summary"] and entry["description"], name)

    def test_aliases_reach_the_screens(self):
        for word, name in (("map", "map"), ("country", "map"),
                           ("geography", "map"), ("education", "education"),
                           ("literacy", "education"), ("schools", "education"),
                           ("demography", "demography"),
                           ("divergence", "divergence")):
            command, error = parse_typed(word)
            self.assertIsNone(error, word)
            self.assertEqual(command["cmd"], name, word)

    def test_population_no_longer_swallows_the_alias(self):
        self.assertEqual(command_registry.resolve("demography")["name"], "demography")


if __name__ == "__main__":
    unittest.main()
