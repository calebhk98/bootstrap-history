"""Complaints/517: the year's merchant tonnes are tabulated by route length (days of the haul) and value per kilogram."""

QUICK_TOPIC = True

import unittest

from sim.economy import carried_by_length

DAYS = {("a", "b"): 10.0, ("a", "c"): 100.0, ("a", "d"): 400.0, ("a", "e"): 800.0, ("a", "f"): 30.0}
# {good: {origin: {destination: [tonnes, value at the origin, value at the destination]}}}
CARRIED = {
    "salt": {"a": {"b": [4.0, 4000.0, 5000.0], "c": [2.0, 2000.0, 3000.0], "f": [1.0, 1000.0, 1200.0]}},
    "silk": {"a": {"d": [0.5, 500000.0, 600000.0], "e": [0.25, 250000.0, 300000.0]}},
}


def days(origin, destination):
    return DAYS[(origin, destination)]


class TabulateTests(unittest.TestCase):
    def test_each_route_is_binned_by_its_length_and_its_value_per_kilogram(self):
        bands = {(band.length, band.value): band.tonnes for band in carried_by_length.tabulate(CARRIED, days)}
        # a haul of exactly an edge is in the band below it (salt a to f: 30 days; salt is worth 1 a kilogram)
        self.assertEqual(bands, {("<=30 days", "<=1 per kg"): 5.0, ("<=365 days", "<=1 per kg"): 2.0,
                                 ("<=730 days", ">100 per kg"): 0.5, (">730 days", ">100 per kg"): 0.25})

    def test_the_value_at_the_origin_is_kept_with_the_tonnes(self):
        bands = carried_by_length.tabulate(CARRIED, days)
        self.assertEqual([band.value_at_origin for band in bands], [5000.0, 2000.0, 500000.0, 250000.0])

    def test_tonnes_by_length_add_the_value_bands(self):
        self.assertEqual(carried_by_length.by_length(carried_by_length.tabulate(CARRIED, days)),
                         {"<=30 days": 5.0, "<=365 days": 2.0, "<=730 days": 0.5, ">730 days": 0.25})

    def test_a_route_with_no_price_is_unpriced(self):
        bands = carried_by_length.tabulate({"x": {"a": {"b": [3.0, 0.0, 0.0]}}}, days)
        self.assertEqual([(band.value, band.tonnes) for band in bands], [("unpriced", 3.0)])

    def test_an_unreachable_route_is_in_the_longest_band(self):
        bands = carried_by_length.tabulate({"x": {"a": {"b": [3.0, 3000.0, 3000.0]}}}, lambda origin, destination: float("inf"))
        self.assertEqual([band.length for band in bands], [">730 days"])

    def test_nothing_carried_gives_no_bands(self):
        self.assertEqual(carried_by_length.tabulate({}, days), [])
        self.assertEqual(carried_by_length.tabulate({"x": {"a": {"b": [0.0, 0.0, 0.0]}}}, days), [])


if __name__ == "__main__":
    unittest.main()
