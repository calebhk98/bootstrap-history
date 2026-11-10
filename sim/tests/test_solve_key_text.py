"""`payload_text` writes the text `json.dumps` wrote for the solve key, and writes it again when a kept input changed."""

QUICK_TOPIC = True

import random
import unittest

from sim.prices.solve_key_text import payload_text
from sim.tests.solve_key_plain import payload_by_dumping


def _catalogue(generator, size):
    return {"entry%d" % number: {"inputs": {"wood": generator.random(), "iron": generator.randint(0, 5)},
                                 "tags": [generator.choice(["a", "b", True, None, 2.0, 2]) for _ in range(3)]}
            for number in range(size)}


class PayloadTextTests(unittest.TestCase):
    def test_written_out_inputs(self):
        inputs = {"gates": ["b", "a"], "starting_rate": 0.05, "territory": {"x": 1}, "rent": None}
        self.assertEqual(payload_text(inputs, "digest"), payload_by_dumping(inputs, "digest"))
        self.assertEqual(payload_text({}, "digest"), payload_by_dumping({}, "digest"))

    def test_random_inputs_with_a_large_catalogue_asked_again(self):
        for seed in range(25):
            generator = random.Random(seed)
            catalogue = _catalogue(generator, generator.choice([5, 150, 400]))
            for _ in range(3):
                inputs = {"production": catalogue, "gates": sorted(generator.sample("abcdef", 3)), "interest_rate": generator.random(),
                          "admitted": {"k1", "k2"} if generator.random() < 0.5 else set(), "rent": [["wood", 1.5]]}
                self.assertEqual(payload_text(inputs, "env%d" % seed), payload_by_dumping(inputs, "env%d" % seed))

    def test_a_catalogue_changed_in_place_is_written_again(self):
        catalogue = _catalogue(random.Random(1), 200)
        inputs = {"production": catalogue}
        payload_text(inputs, "e")
        catalogue["entry7"]["inputs"]["wood"] = 99.0
        self.assertEqual(payload_text(inputs, "e"), payload_by_dumping(inputs, "e"))
        catalogue["entry7"]["inputs"]["wood"] = 99      # the same value of another type writes another text
        self.assertEqual(payload_text(inputs, "e"), payload_by_dumping(inputs, "e"))
        self.assertTrue('"wood": 99}' in payload_text(inputs, "e"))
