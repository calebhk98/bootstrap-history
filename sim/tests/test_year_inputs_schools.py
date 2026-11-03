"""The schools a game's seats hold reach the economy's year inputs: one `School` per trade and seat, in the labour area of the
seat's base tile. Each test calls `YearInputsBuilder.seat_schools` on stand-in seats."""
QUICK_TOPIC = True

import contextlib
import types
import unittest

from sim.economy.setup import labour_area
from sim.markets.port_year_inputs import YearInputsBuilder


def builder(schools_by_seat):
    acting = []

    @contextlib.contextmanager
    def act_as(seat_id):
        acting.append(seat_id)
        yield

    labour = types.SimpleNamespace(trade_schools=lambda: schools_by_seat[acting[-1]], base_tile=lambda: "tile:" + acting[-1])
    world = types.SimpleNamespace(state=types.SimpleNamespace(seats_playing=lambda: sorted(schools_by_seat)),
                                  scenario=types.SimpleNamespace(act_as=act_as), labour=labour)
    agent = types.SimpleNamespace(tile_in_economy=lambda tile: tile)
    return YearInputsBuilder(world, agent, None)


class SeatSchoolsTests(unittest.TestCase):
    def test_each_seat_with_seats_has_a_school_per_trade_in_its_base_tile_area(self):
        schools = builder({"a": {"smith": 3.0, "carter": 0.0}, "b": {"baker": 2.0}}).seat_schools()
        self.assertEqual([(each.owner, each.trade, each.area, each.seats) for each in schools],
                         [("a", "smith", labour_area("tile:a"), 3.0), ("b", "baker", labour_area("tile:b"), 2.0)])

    def test_a_seat_with_no_school_adds_none(self):
        self.assertEqual(builder({"a": {}}).seat_schools(), ())


if __name__ == "__main__":
    unittest.main()
