"""Which civilisations the runner builds ahead of the topics it runs: only those the chosen topics build."""

QUICK_TOPIC = True

import os
import tempfile
import unittest

from sim.tests import discovery
from sim.tests.warming import DEFAULT_CIVILISATION, civilisations_to_warm


class CivilisationsToWarmTests(unittest.TestCase):
    def test_quick_topics_alone_warm_nothing(self):
        self.assertEqual(civilisations_to_warm(["a"], {"a"}, {}), [])

    def test_a_topic_that_declares_no_civilisation_warms_nothing(self):
        self.assertEqual(civilisations_to_warm(["fixture"], set(), {"fixture": ()}), [])

    def test_a_topic_that_declares_nothing_warms_the_default_start(self):
        self.assertEqual(civilisations_to_warm(["game"], set(), {}), [DEFAULT_CIVILISATION])

    def test_declared_civilisations_are_warmed_once_in_sorted_order(self):
        declared = {"one": ("rome_100ad", "han"), "two": ("han",), "fixture": ()}
        self.assertEqual(civilisations_to_warm(["one", "two", "fixture"], set(), declared), ["han", "rome_100ad"])

    def test_only_the_chosen_topics_count(self):
        declared = {"one": ("han",), "other": ("inca",)}
        self.assertEqual(civilisations_to_warm(["one"], set(), declared), ["han"])

    def test_declarations_are_read_from_the_topic_file_without_importing_it(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, text in (("a", "CIVILISATIONS = ('han',)\nraise RuntimeError('imported')\n"),
                               ("b", "CIVILISATIONS = ()\n"), ("c", "x = 1\n")):
                with open(os.path.join(directory, "test_%s.py" % name), "w", encoding="utf-8") as handle:
                    handle.write(text)
            self.assertEqual(discovery.discover_civilisations(directory), {"a": ("han",), "b": ()})


if __name__ == "__main__":
    unittest.main()
