"""Complaint 476: an entrant sees a concern from where its country sits, and a country sits where its people are. The
home country's profile is placed at the cast's stated location, else at the civilisation's default base tile; the
government actor of the cast is placed at its profile's location. `profile_from_civilisation` and
`cast_from_civilisations` are called on civilisations built here. Sight itself (exposure against
PLAYER_VISIBLE_EXPOSURE, distance thinning it) is test_actor_fog and test_seat_sight."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.agents.cast import cast_from_civilisations, profile_from_civilisation
from sim.labour.labour_settlement import SettlementMixin

TILES = ["algeria_01", "algeria_02", "algeria_03"]


class HomeLocationTests(unittest.TestCase):
    def test_a_country_with_no_stated_location_sits_at_the_default_base_tile_of_its_land(self):
        profile = profile_from_civilisation({"id": "alpha", "home_tiles": TILES})
        self.assertIsNotNone(profile.location)
        self.assertEqual(profile.location, "algeria_01")

    def test_a_stated_location_overrides_the_default(self):
        profile = profile_from_civilisation({"id": "alpha", "home_tiles": TILES, "cast": {"location": "algeria_03"}})
        self.assertEqual(profile.location, "algeria_03")

    def test_a_country_with_no_land_has_no_location(self):
        self.assertIsNone(profile_from_civilisation({"id": "alpha"}).location)

    def test_the_governments_actor_is_placed_where_the_country_sits(self):
        civilisation = {"id": "alpha", "home_tiles": TILES}
        home_country, entries, profiles = cast_from_civilisations(civilisation, [])
        government = [entry for entry in entries if entry.actor_id == "government:" + home_country]
        self.assertEqual([entry.location for entry in government], [profiles[home_country].location])


class FounderBase(SettlementMixin):
    def __init__(self, chosen):
        self._world = SimpleNamespace(home_tiles_held=lambda: TILES, state=SimpleNamespace(household=SimpleNamespace(base_tile=chosen)))


class FounderBaseTileTests(unittest.TestCase):
    def test_a_founder_who_has_chosen_no_base_works_from_the_tile_the_home_country_sits_at(self):
        self.assertEqual(FounderBase(None).base_tile(), "algeria_01")

    def test_a_chosen_held_tile_is_the_base(self):
        self.assertEqual(FounderBase("algeria_03").base_tile(), "algeria_03")

    def test_a_chosen_tile_the_nation_does_not_hold_is_not_a_base(self):
        self.assertIn(FounderBase("elsewhere_99").base_tile(), TILES)


if __name__ == "__main__":
    unittest.main()
