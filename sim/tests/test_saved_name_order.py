"""`in_saved_order` sorts market rows as the lambda sort `name.replace("|", "\\x00")` did."""

QUICK_TOPIC = True

import random
import unittest

import numpy

from sim.economy.saved_name_order import in_saved_order, saved_rank


def plain_order(rows, names):
    """The old sort of `MarketFigures.sorted_named`, as row numbers."""
    return sorted(rows, key=lambda row: names[row].replace("|", "\x00"))


class SavedNameOrderTests(unittest.TestCase):
    def test_written_out_names(self):
        names = ["wheat|rome", "wheat|rome_2", "wheat 2|rome", "iron|ostia", "wheat|ostia"]
        rows = numpy.array([0, 1, 2, 3, 4])
        self.assertEqual(in_saved_order(rows, names).tolist(), plain_order([0, 1, 2, 3, 4], names))
        self.assertEqual(in_saved_order(rows, names).tolist(), [3, 4, 0, 1, 2])

    def test_only_the_rows_asked_for(self):
        names = ["b|x", "a|x", "c|x", "a|y"]
        self.assertEqual(in_saved_order(numpy.array([2, 0, 3]), names).tolist(), [3, 0, 2])

    def test_random_names(self):
        for seed in range(30):
            generator = random.Random(seed)
            names = sorted({"%s|%s" % (generator.choice(["a", "a b", "ab", "b"]), generator.choice(["x", "xy", "x_1", "y"])) +
                            str(generator.randint(0, 40)) for _ in range(30)})
            generator.shuffle(names)
            rows = sorted(generator.sample(range(len(names)), len(names) // 2))
            self.assertEqual(in_saved_order(numpy.array(rows), names).tolist(), plain_order(rows, names), seed)

    def test_a_changed_list_is_ranked_again(self):
        names = ["b|x", "a|x"]
        self.assertEqual(saved_rank(names).tolist(), [1, 0])
        names[0] = "0|x"
        self.assertEqual(saved_rank(names).tolist(), [0, 1])


if __name__ == "__main__":
    unittest.main()
