"""The root's registry operation behind `AddSeat` (`seat_registry.register_seat`): a seat built from the template joins the registry
with the standing policy a new seat starts with; an id already taken is refused with the cause `seat_exists` and changes nothing."""

QUICK_TOPIC = True

import types
import unittest

from sim.engine import seat_registry
from sim.engine.bridge_land import MODS_DIR
from sim.engine.seat_defaults import default_policy
from sim.seats.state import COUNTRY_SEAT


def registry_over(seats, manual=False):
    return types.SimpleNamespace(state=types.SimpleNamespace(seats=seats), manual=manual, assembly=None, mods_dir=MODS_DIR)


class RegisterSeat(unittest.TestCase):
    def test_a_household_seat_joins_the_registry_with_the_templates_goal_and_the_default_policy(self):
        seats = {}
        answer = seat_registry.register_seat(registry_over(seats), "second", {"goal": "steel", "scholars": 2.0})
        self.assertIsNone(answer)
        slot = seats["second"].modules["seats"]
        self.assertEqual((slot.goal, slot.policy), ("steel", default_policy(False)))

    def test_a_player_who_plays_by_hand_gets_the_manual_policy(self):
        seats = {}
        seat_registry.register_seat(registry_over(seats, manual=True), "second", {})
        self.assertEqual(seats["second"].modules["seats"].policy, default_policy(True))

    def test_a_country_seat_is_built_without_a_household_founder(self):
        seats = {}
        seat_registry.register_seat(registry_over(seats), "han", {"kind": COUNTRY_SEAT, "country": "han"})
        self.assertEqual((seats["han"].founder, seats["han"].modules["seats"].country), (None, "han"))

    def test_an_id_already_taken_is_refused_and_the_registry_is_unchanged(self):
        taken = object()
        seats = {"second": taken}
        answer = seat_registry.register_seat(registry_over(seats), "second", {})
        self.assertEqual((answer.cause, seats), ("seat_exists", {"second": taken}))


if __name__ == "__main__":
    unittest.main()
