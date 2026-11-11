"""`BookStore.agent_numbers_batch`, `good_numbers_batch` and `tile_numbers_batch` number the names new to the book together, sorted among
themselves, exactly as `agent_number` (`good_number`, `tile_number`) gives them one at a time in sorted order."""

QUICK_TOPIC = True

import random
import unittest

from sim.book import Book


def one_at_a_time(book, number_of, names):
    """The numbers of `names` when the new ones are numbered one by one in sorted order."""
    for name in sorted(set(names)):
        number_of(name)
    return [number_of(name) for name in names]


class BatchNumberTests(unittest.TestCase):
    def test_written_out_agents(self):
        batch, plain = Book(), Book()
        batch.agent_number("known")
        plain.agent_number("known")
        names = ["zeta", "alpha", "known", "zeta", "mid"]
        self.assertEqual(batch.agent_numbers_batch(names), one_at_a_time(plain, plain.agent_number, names))
        self.assertEqual(batch.agent_ids.name_list, plain.agent_ids.name_list)

    def test_seeded_random_names_of_each_kind(self):
        generator = random.Random(5)
        batch, plain = Book(), Book()
        for _ in range(6):
            names = ["n%02d" % generator.randrange(40) for _ in range(25)]
            self.assertEqual(batch.agent_numbers_batch(names), one_at_a_time(plain, plain.agent_number, names))
            self.assertEqual(batch.good_numbers_batch(names), one_at_a_time(plain, plain.good_number, names))
            self.assertEqual(batch.tile_numbers_batch(names), one_at_a_time(plain, plain.tile_number, names))
        self.assertEqual((batch.agent_ids.name_list, batch.good_ids.name_list, batch.tile_ids.name_list),
                         (plain.agent_ids.name_list, plain.good_ids.name_list, plain.tile_ids.name_list))


if __name__ == "__main__":
    unittest.main()
