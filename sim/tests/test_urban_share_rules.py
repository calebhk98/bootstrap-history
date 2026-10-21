"""Complaint 603: the urban share is bounded by the food surplus a town can draw at the carriage cost of grain.

Each test calls the rule on inputs built in the test: the farm surplus, the delivered share of a tonne, the ceilings of
towns sharing a hinterland, the opening split of the typed share, and the saved shares' effect on the readers."""
import unittest

from sim.geography import api as geography_api
from sim.world import urban_share

KCAL_PER_PERSON = 900000.0


class FarmSurplusTests(unittest.TestCase):
    def test_a_richer_harvest_per_worker_feeds_more_townspeople(self):
        poor = urban_share.farm_surplus_people(1000.0, 2.5e6, 2.0, KCAL_PER_PERSON)
        rich = urban_share.farm_surplus_people(1000.0, 3.5e6, 2.0, KCAL_PER_PERSON)
        self.assertGreater(rich, poor)

    def test_a_harvest_that_only_feeds_the_farm_households_leaves_no_surplus(self):
        self.assertEqual(urban_share.farm_surplus_people(1000.0, 2.0 * KCAL_PER_PERSON, 2.0, KCAL_PER_PERSON), 0.0)
        self.assertEqual(urban_share.farm_surplus_people(1000.0, 1.0 * KCAL_PER_PERSON, 2.0, KCAL_PER_PERSON), 0.0)

    def test_more_dependents_per_worker_leave_less_surplus(self):
        few = urban_share.farm_surplus_people(1000.0, 4.0 * KCAL_PER_PERSON, 1.5, KCAL_PER_PERSON)
        many = urban_share.farm_surplus_people(1000.0, 4.0 * KCAL_PER_PERSON, 2.5, KCAL_PER_PERSON)
        self.assertGreater(few, many)


class DeliveredShareTests(unittest.TestCase):
    def test_carriage_costing_the_tonnes_worth_delivers_nothing(self):
        self.assertEqual(urban_share.delivered_share(2000.0, 2000.0), 0.0)
        self.assertEqual(urban_share.delivered_share(5000.0, 2000.0), 0.0)

    def test_no_route_delivers_nothing_not_a_free_tonne(self):
        self.assertEqual(urban_share.delivered_share(None, 2000.0), 0.0)

    def test_cheaper_carriage_delivers_more(self):
        self.assertGreater(urban_share.delivered_share(400.0, 2000.0), urban_share.delivered_share(800.0, 2000.0))


class TownCeilingTests(unittest.TestCase):
    def test_a_town_with_no_farms_of_its_own_lives_on_what_is_carried_in(self):
        ceilings = urban_share.town_ceilings({"farm": 1000.0, "town": 0.0}, {"farm": {"town": 500.0}},
                                             {"farm": 2000.0, "town": 2000.0})
        self.assertGreater(ceilings["town"], 0.0)

    def test_a_richer_surplus_raises_the_ceiling(self):
        carriage = {"farm": {"town": 500.0}}
        value = {"farm": 2000.0, "town": 2000.0}
        poor = urban_share.town_ceilings({"farm": 500.0, "town": 0.0}, carriage, value)["town"]
        rich = urban_share.town_ceilings({"farm": 1000.0, "town": 0.0}, carriage, value)["town"]
        self.assertGreater(rich, poor)

    def test_cheaper_carriage_widens_the_draw(self):
        surplus = {"near": 1000.0, "far": 1000.0, "town": 0.0}
        value = {"near": 2000.0, "far": 2000.0, "town": 2000.0}
        dear = urban_share.town_ceilings(surplus, {"near": {"town": 600.0}, "far": {"town": 1900.0}}, value)["town"]
        cheap = urban_share.town_ceilings(surplus, {"near": {"town": 300.0}, "far": {"town": 950.0}}, value)["town"]
        self.assertGreater(cheap, dear)

    def test_a_farm_beyond_reach_adds_nothing(self):
        surplus = {"near": 1000.0, "far": 1000.0, "town": 0.0}
        value = {"near": 2000.0, "far": 2000.0, "town": 2000.0}
        with_far = urban_share.town_ceilings(surplus, {"near": {"town": 300.0}, "far": {"town": 5000.0}}, value)["town"]
        without_far = urban_share.town_ceilings({"near": 1000.0, "town": 0.0}, {"near": {"town": 300.0}}, value)["town"]
        self.assertAlmostEqual(with_far, without_far)

    def test_a_surplus_is_not_counted_twice_across_towns(self):
        surplus = {"farm": 1000.0, "a": 0.0, "b": 0.0}
        carriage = {"farm": {"a": 200.0, "b": 200.0}}
        value = {"farm": 2000.0, "a": 2000.0, "b": 2000.0}
        ceilings = urban_share.town_ceilings(surplus, carriage, value)
        self.assertLessEqual(sum(ceilings.values()), 1000.0 + 1e-9)


class PortAndLandlockedTownTests(unittest.TestCase):
    """The same hinterland feeds a larger town by sea than by land (carriage costs are geography's route costs)."""

    @classmethod
    def setUpClass(cls):
        # two coastal farm tiles with a port tile between them on the coast, and an inland tile behind them both
        records = {
            "farm_west": {"lat": 10.0, "lon": -150.0, "coastal": True, "borders": ["port", "inland"]},
            "port": {"lat": 10.0, "lon": -146.5, "coastal": True, "borders": ["farm_west", "farm_east", "inland"]},
            "farm_east": {"lat": 10.0, "lon": -143.0, "coastal": True, "borders": ["port", "inland"]},
            "inland": {"lat": 13.5, "lon": -146.5, "coastal": False, "borders": ["farm_west", "port", "farm_east"]},
        }
        cls.map = geography_api.map_of_tiles(records)
        modes = ["cart", "foot", "sail"]
        cls.carriage = {farm: geography_api.route_costs([farm], modes, world_map=cls.map, within=["port", "inland"])
                        for farm in ("farm_west", "farm_east")}

    def _ceilings(self, carriage):
        surplus = {"farm_west": 1000.0, "farm_east": 1000.0, "port": 0.0, "inland": 0.0}
        value = {tile: 2000.0 for tile in surplus}
        return urban_share.town_ceilings(surplus, carriage, value)

    def test_the_port_carries_more_than_the_landlocked_town_with_the_same_hinterland(self):
        ceilings = self._ceilings(self.carriage)
        self.assertGreater(ceilings["port"], ceilings["inland"])

    def test_without_ships_the_port_has_no_advantage(self):
        land_only = {farm: geography_api.route_costs([farm], ["cart", "foot"], world_map=self.map, within=["port", "inland"])
                     for farm in ("farm_west", "farm_east")}
        by_land = self._ceilings(land_only)
        by_sea = self._ceilings(self.carriage)
        self.assertGreater(by_sea["port"], by_land["port"])


class OpeningSharesTests(unittest.TestCase):
    def test_the_typed_share_is_shared_by_what_each_town_can_feed(self):
        people = {"port": 100000.0, "inland": 100000.0}
        shares = urban_share.opening_shares(people, {"port": 30000.0, "inland": 10000.0}, 0.1)
        urban = {tile: shares[tile] * people[tile] for tile in people}
        self.assertAlmostEqual(sum(urban.values()), 20000.0)
        self.assertGreater(urban["port"], urban["inland"])

    def test_no_town_is_given_more_than_it_can_feed(self):
        people = {"port": 100000.0, "inland": 100000.0}
        shares = urban_share.opening_shares(people, {"port": 30000.0, "inland": 1000.0}, 0.2)
        self.assertLessEqual(shares["inland"] * people["inland"], 1000.0 + 1e-6)
        self.assertLessEqual(shares["port"] * people["port"], 30000.0 + 1e-6)

    def test_a_typed_share_the_land_cannot_carry_is_not_forced(self):
        people = {"a": 100000.0}
        shares = urban_share.opening_shares(people, {"a": 5000.0}, 0.5)
        self.assertAlmostEqual(shares["a"] * people["a"], 5000.0)


class BandTests(unittest.TestCase):
    BANDS = {"rome": {"low": 0.1, "high": 0.15}, "none": None}

    def test_a_share_inside_the_band_passes_and_outside_fails(self):
        band = urban_share.band_for("rome", self.BANDS)
        self.assertTrue(urban_share.within_band(0.12, band))
        self.assertFalse(urban_share.within_band(0.3, band))

    def test_a_civilisation_with_no_source_has_no_band_not_a_zero_band(self):
        self.assertIsNone(urban_share.band_for("none", self.BANDS))
        self.assertIsNone(urban_share.band_for("unknown", self.BANDS))
        self.assertIsNone(urban_share.within_band(0.2, None))


if __name__ == "__main__":
    unittest.main()
