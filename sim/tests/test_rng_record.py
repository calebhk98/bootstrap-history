"""Complaint 640 (a Han break test): a resumed game carries on the same dice, so a project at its threshold does not re-roll its
failure check on every resume. `rng_record` writes a generator's state as JSON data and `restore_rng` puts it back, each
called on generators built here."""
QUICK_TOPIC = True

import json
import random
import unittest

from sim.engine.rng_record import restore_rng, rng_record


class RngRecord(unittest.TestCase):
    def test_a_generator_restored_from_its_record_draws_what_the_original_draws_next(self):
        original = random.Random(7)
        original.random()
        original.gauss(0.0, 1.0)
        resumed = random.Random(99)
        restore_rng(resumed, rng_record(original))
        self.assertEqual([original.random() for _ in range(5)], [resumed.random() for _ in range(5)])

    def test_the_record_survives_being_written_as_json_text_and_read_back(self):
        original = random.Random(7)
        original.random()
        resumed = random.Random(99)
        restore_rng(resumed, json.loads(json.dumps(rng_record(original))))
        self.assertEqual([original.random() for _ in range(5)], [resumed.random() for _ in range(5)])

    def test_the_record_is_plain_lists_and_numbers(self):
        record = rng_record(random.Random(7))
        self.assertIsInstance(record, list)
        self.assertIsInstance(record[1], list)
        json.dumps(record)

    def test_a_generator_that_cannot_give_its_state_has_no_record(self):
        self.assertIsNone(rng_record(object()))


if __name__ == "__main__":
    unittest.main()
