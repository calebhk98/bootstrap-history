"""`replaced` copies a plain dataclass the way `dataclasses.replace` does and falls back to it for a class it
cannot copy through its dictionary."""

QUICK_TOPIC = True

import dataclasses
import unittest

from sim.economy.producers import Producer
from sim.economy.replaced import replaced


@dataclasses.dataclass(frozen=True)
class Checked:
    amount: float
    note: str = ""

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("negative")


@dataclasses.dataclass
class Loose:
    amount: float
    items: list = dataclasses.field(default_factory=list)


class ReplacedTest(unittest.TestCase):
    def test_a_frozen_record_is_copied_with_the_changes(self):
        original = Producer("a", "owner", "recipe", "tile", 2.0)
        changed = replaced(original, capacity_runs=3.0, years_of_loss=4)
        self.assertEqual(changed, dataclasses.replace(original, capacity_runs=3.0, years_of_loss=4))
        self.assertEqual(original.capacity_runs, 2.0)
        self.assertIsNot(changed.expected_prices, None)

    def test_an_unknown_field_is_refused_like_replace(self):
        with self.assertRaises(TypeError):
            replaced(Producer("a", "owner", "recipe", "tile", 2.0), no_such_field=1)

    def test_a_class_with_a_post_init_goes_the_long_way(self):
        with self.assertRaises(ValueError):
            replaced(Checked(1.0), amount=-1.0)

    def test_a_mutable_record_is_a_new_object(self):
        original = Loose(1.0)
        changed = replaced(original, amount=2.0)
        self.assertEqual((original.amount, changed.amount), (1.0, 2.0))
        self.assertIsNot(original, changed)


if __name__ == "__main__":
    unittest.main()
