"""`merchants_book_kernel.rooms_of` (the room of every held route of a merchant in one call) gives `room_of` for each pair and the rule of
`merchants_shares.room_left` (`merchants_room_plain.plain_rooms`), on written-out and seeded random markets; equal to a relative 1e-12."""
QUICK_TOPIC = True

import random
import unittest

import numpy

from sim.economy import merchants_book_kernel
from sim.economy.merchants_shares import MERCHANT_GROUP_SHARE, MERCHANT_SOURCE_SHARE
from sim.tests.merchants_room_plain import plain_rooms

OWN_SHARE = 0.5


def compiled_rooms(destinations, sources, volumes, held, group_into, group_out):
    return merchants_book_kernel.rooms_of(
        numpy.array(destinations, numpy.int64), numpy.array(sources, numpy.int64), numpy.array(volumes, numpy.float64),
        numpy.array(held, numpy.float64), numpy.zeros(len(volumes)), numpy.array(group_into, numpy.float64),
        numpy.array(group_out, numpy.float64), OWN_SHARE, MERCHANT_GROUP_SHARE, MERCHANT_SOURCE_SHARE).tolist()


class RoomsOf(unittest.TestCase):

    def test_a_written_out_market(self):
        nan = float("nan")
        volumes, held = [100.0, 40.0, nan, nan], [0.0, 10.0, 0.0, 0.0]
        group_into, group_out = [0.0, 50.0, 0.0, 0.0], [90.0, 0.0, 0.0, 0.0]
        pairs = [(1, 0), (0, 1), (2, 0), (3, 1), (3, 2), (1, 1)]
        destinations, sources = zip(*pairs)
        rooms = compiled_rooms(destinations, sources, volumes, held, group_into, group_out)
        self.assertEqual(rooms, [10.0, 40.0, 10.0, 20.0, float("inf"), 10.0])
        self.assertEqual(rooms, plain_rooms(destinations, sources, volumes, held, group_into, group_out, OWN_SHARE))

    def test_no_pairs(self):
        self.assertEqual(compiled_rooms([], [], [1.0], [0.0], [0.0], [0.0]), [])

    def test_random_markets(self):
        for seed in range(40):
            rng = random.Random(seed)
            slots = rng.randint(1, 12)
            volumes = [rng.choice([float("nan"), rng.uniform(0.0, 500.0)]) for _slot in range(slots)]
            held = [rng.choice([0.0, rng.uniform(0.0, 80.0)]) for _slot in range(slots)]
            group_into = [rng.choice([0.0, rng.uniform(0.0, 900.0)]) for _slot in range(slots)]
            group_out = [rng.choice([0.0, rng.uniform(0.0, 600.0)]) for _slot in range(slots)]
            destinations = [rng.randrange(slots) for _pair in range(rng.randint(0, 20))]
            sources = [rng.randrange(slots) for _pair in destinations]
            rooms = compiled_rooms(destinations, sources, volumes, held, group_into, group_out)
            expected = plain_rooms(destinations, sources, volumes, held, group_into, group_out, OWN_SHARE)
            for found, wanted in zip(rooms, expected):
                self.assertAlmostEqual(found, wanted, delta=1e-12 * max(1.0, abs(wanted)) if wanted != float("inf") else 0)
            self.assertEqual([each == float("inf") for each in rooms], [each == float("inf") for each in expected])


if __name__ == "__main__":
    unittest.main()
