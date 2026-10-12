"""The runner's time limit is per topic, also inside a batch of quick topics: the clock restarts when a topic
finishes, and a stopped batch fails only the topic it was running while the ones after it run again."""

QUICK_TOPIC = True

import os
import tempfile
import time
import unittest

from sim.tests import __main__ as runner


class BatchTimeLimitTests(unittest.TestCase):
    def test_the_clock_starts_at_the_worker_start_before_any_topic_finishes(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = os.path.join(directory, "batch.json")
            self.assertEqual(runner._current_topic_started(100.0, missing), 100.0)

    def test_the_clock_restarts_when_a_finished_topic_is_written(self):
        with tempfile.TemporaryDirectory() as directory:
            result_path = os.path.join(directory, "batch.json")
            with open(result_path, "w", encoding="utf-8") as handle:
                handle.write("{}")
            written = time.time() + 50.0
            os.utime(result_path, (written, written))
            self.assertEqual(runner._current_topic_started(written - 100.0, result_path), written)

    def test_a_stopped_batch_fails_the_running_topic_and_returns_the_rest(self):
        slugs = ["first", "second", "third", "fourth"]
        results = {"first": {"seconds": 1.0}}
        self.assertEqual(runner._split_stopped_batch(slugs, results), ("second", ["third", "fourth"]))

    def test_a_stopped_single_topic_has_nothing_left_to_run(self):
        self.assertEqual(runner._split_stopped_batch(["only"], {}), ("only", []))


if __name__ == "__main__":
    unittest.main()
