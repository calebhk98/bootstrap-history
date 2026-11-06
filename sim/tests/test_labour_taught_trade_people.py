"""People in a trade only the founder teaches: an estimate from staff and school seats until a school exists and the labour core
holds the trade's people, then the core's own count."""

QUICK_TOPIC = True

import types
import unittest

from sim.labour import labour_supply


def supply_with(employed, seats, in_core):
    world = types.SimpleNamespace(workforce=types.SimpleNamespace(trade_schools=seats))
    book = types.SimpleNamespace(employed=lambda trade: employed, core_people_by_trade=lambda: in_core)
    return labour_supply.Supply(world, book=book, capacity=None, settlement=None, trades=None)


class TaughtTradePeople(unittest.TestCase):

    def test_with_no_school_the_estimate_is_the_staff_and_their_students(self):
        supply = supply_with(4.0, {}, {"mill": 99.0})
        self.assertEqual(supply._taught_trade_people("mill"), 4.0 * supply.TAUGHT_TRADE_SUPPLY_MULTIPLIER)

    def test_once_a_school_exists_the_cores_people_of_the_trade_are_counted(self):
        self.assertEqual(supply_with(4.0, {"mill": 30.0}, {"mill": 17.0})._taught_trade_people("mill"), 17.0)

    def test_once_a_school_exists_and_the_core_holds_nobody_the_count_is_nobody(self):
        self.assertEqual(supply_with(4.0, {"mill": 30.0}, {})._taught_trade_people("mill"), 0.0)

    def test_before_the_core_has_opened_the_estimate_stands(self):
        supply = supply_with(4.0, {"mill": 30.0}, None)
        self.assertEqual(supply._taught_trade_people("mill"), 4.0 * supply.TAUGHT_TRADE_SUPPLY_MULTIPLIER + 30.0)


if __name__ == "__main__":
    unittest.main()
