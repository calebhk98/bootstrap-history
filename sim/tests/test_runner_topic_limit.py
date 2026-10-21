"""The rule that picks a topic's time limit: --topic-seconds when given, else the larger of the default and what the
topic file declares with a module-level TOPIC_SECONDS."""

QUICK_TOPIC = True

import os
import tempfile
import unittest

from sim.tests import __main__ as runner
from sim.tests import discovery


class TopicLimitTests(unittest.TestCase):
    def test_a_topic_that_declares_nothing_gets_the_default(self):
        self.assertEqual(runner.topic_limit(None, 120.0, None), 120.0)

    def test_a_larger_declared_limit_replaces_the_default(self):
        self.assertEqual(runner.topic_limit(900.0, 120.0, None), 900.0)

    def test_a_smaller_declared_limit_does_not_lower_the_default(self):
        self.assertEqual(runner.topic_limit(30.0, 120.0, None), 120.0)

    def test_an_explicit_command_line_limit_beats_the_declared_one(self):
        self.assertEqual(runner.topic_limit(900.0, 120.0, 240.0), 240.0)

    def test_a_limit_is_read_from_the_topic_file_without_importing_it(self):
        with tempfile.TemporaryDirectory() as directory:
            with open(os.path.join(directory, "test_slow_one.py"), "w", encoding="utf-8") as handle:
                handle.write("TOPIC_SECONDS = 600\nraise RuntimeError('imported')\n")
            with open(os.path.join(directory, "test_plain.py"), "w", encoding="utf-8") as handle:
                handle.write("X = 1\n")
            self.assertEqual(discovery.discover_topic_seconds(directory), {"slow_one": 600.0})


if __name__ == "__main__":
    unittest.main()
