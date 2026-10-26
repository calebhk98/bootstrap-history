"""The disease module's rules (`sim/disease/rules.py`): who lives on each tile, what the diseases of a tile take in a year, which
tiles are the frontier, and what a seat is told. Each is called on plain values."""
QUICK_TOPIC = True

import unittest

from sim.disease.api import rules

BANDS = ("children", "working_age", "elderly")


class PeopleByTileTest(unittest.TestCase):
    def test_stored_regions_covering_the_held_tiles_are_the_people(self):
        stored = {"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]}
        found = rules.people_by_tile(["a", "b"], stored, ["a", "b"], BANDS, {}, lambda: self.fail("shares are not needed"))
        self.assertEqual(found, {"a": {"children": 1.0, "working_age": 2.0, "elderly": 3.0},
                                 "b": {"children": 4.0, "working_age": 5.0, "elderly": 6.0}})

    def test_regions_that_miss_a_held_tile_fall_back_to_the_nations_bands_by_share(self):
        national = {"children": 100.0, "working_age": 200.0, "elderly": 50.0}
        found = rules.people_by_tile(["a", "b"], {"a": [1.0, 2.0, 3.0]}, ["a", "b"], BANDS, national, lambda: {"a": 0.25, "b": 0.75})
        self.assertEqual(found["a"], {"children": 25.0, "working_age": 50.0, "elderly": 12.5})
        self.assertEqual(found["b"]["working_age"], 150.0)

    def test_no_stored_regions_also_fall_back(self):
        found = rules.people_by_tile(["a"], None, ["a"], BANDS, {"children": 1.0, "working_age": 1.0, "elderly": 1.0}, lambda: {})
        self.assertEqual(found, {"a": {band: 0.0 for band in BANDS}})


class RegionalLossTest(unittest.TestCase):
    PEOPLE = {"a": {"working_age": 1000.0}, "empty": {"working_age": 0.0}}

    def test_a_held_tile_adds_its_forecast_deaths_over_its_working_age_people_to_the_endemic_rate(self):
        loss = rules.regional_loss(0.01, {"a": {"working_age": 250.0}}, 0.9, self.PEOPLE, "a")
        self.assertAlmostEqual(loss, 0.26)

    def test_a_tile_without_people_has_no_epidemic_loss(self):
        self.assertEqual(rules.regional_loss(0.01, {"empty": {"working_age": 5.0}}, 0.9, self.PEOPLE, "empty"), 0.01)

    def test_a_tile_not_held_takes_the_nations_expected_share(self):
        self.assertAlmostEqual(rules.regional_loss(0.01, {}, 0.25, self.PEOPLE, "elsewhere"), 0.26)

    def test_the_loss_never_exceeds_everyone(self):
        self.assertEqual(rules.regional_loss(0.5, {"a": {"working_age": 900.0}}, 0.0, self.PEOPLE, "a"), 1.0)


class FrontierTilesTest(unittest.TestCase):
    def test_a_held_tile_with_a_neighbour_not_held_is_on_the_frontier(self):
        borders = {"a": ["b"], "b": ["a", "c"], "c": ["b"]}
        self.assertEqual(rules.frontier_tiles(["c", "a", "b"], borders), [])
        self.assertEqual(rules.frontier_tiles(["a", "b"], borders), ["b"])


class SeatLossReportTest(unittest.TestCase):
    def test_a_seat_that_lost_staff_and_cash_is_told_both(self):
        text, took_nothing = rules.seat_loss_report("Plague", 0.25, 10.0, 3.0, "3 coins")
        self.assertEqual(text, "Plague: staff -25%, 3 coins of takings lost while the trade stood idle. Empire-wide, 25% of working-age people died")
        self.assertFalse(took_nothing)

    def test_a_seat_with_nothing_to_take_is_told_so(self):
        text, took_nothing = rules.seat_loss_report("Plague", 0.25, 0.0, 0.0, "")
        self.assertIn("you had nothing it could take", text)
        self.assertTrue(took_nothing)


if __name__ == "__main__":
    unittest.main()
