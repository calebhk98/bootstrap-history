"""Complaint 630: geography's rates and hauls report the carrier-days a tonne-km works, so every reader of a haul
(merchants, freight quotes, supply lines) sizes a fleet and its wear from the same figures."""
QUICK_TOPIC = True

import unittest

from sim.geography import api, routes_carriers, routes_modes, routes_rates, routes_search
from sim.tests.test_geography_routes import small_map


class RateCarrierDays(unittest.TestCase):
    def setUp(self):
        self.world_map = small_map()
        self.mode = routes_modes.modes(self.world_map)["cart"]

    def level_rate(self):
        return routes_rates.compute_rate(self.world_map, self.mode, self.mode["edge_classes"][0], 0.0, 0.0)

    def test_a_rate_reports_the_team_days_a_tonne_km_works(self):
        rate = self.level_rate()
        team = routes_carriers.team_of(self.mode)
        # a team carries its payload the rate's ground pace in a day, class pace included
        self.assertAlmostEqual(rate.team_days, 1.0 / (team[2] * rate.km_per_day))

    def test_a_rate_reports_each_carrier_of_the_team_in_carrier_days(self):
        rate = self.level_rate()
        team = routes_carriers.team_of(self.mode)
        found = {(kind, name): days for kind, name, days in rate.carrier_days}
        self.assertEqual(sorted(found), sorted((kind, name) for kind, name, _count in team[0]))
        for kind, name, count in team[0]:
            self.assertAlmostEqual(found[(kind, name)], count * rate.team_days)

    def test_a_slope_takes_more_team_days_a_tonne_km(self):
        steep = routes_rates.compute_rate(self.world_map, self.mode, self.mode["edge_classes"][0], 0.05, 0.0)
        self.assertGreater(steep.team_days, self.level_rate().team_days)

    def test_a_mode_that_wears_no_team_reports_none(self):
        for mode_id, mode in routes_modes.modes(self.world_map).items():
            if routes_carriers.team_of(mode) is None:
                rate = routes_rates.compute_rate(self.world_map, mode, mode["edge_classes"][0], 0.0, 0.0)
                if rate is not None:
                    self.assertEqual((rate.team_days, rate.carrier_days), (0.0, ()), mode_id)


class HaulCarrierDays(unittest.TestCase):
    def setUp(self):
        self.world_map = small_map()

    def test_a_route_sums_its_legs_team_days_by_mode(self):
        found = routes_search.route(self.world_map, ["a1"], ["a2"], {"cart", "road"})
        total = {}
        for leg in found["legs"]:
            total[leg["mode"]] = total.get(leg["mode"], 0.0) + leg["team_days"]
        self.assertGreater(sum(total.values()), 0.0)
        self.assertEqual(sorted(found["inputs"]["team_days"]), sorted(total))
        for mode, days in total.items():
            self.assertAlmostEqual(found["inputs"]["team_days"][mode], days)

    def test_a_route_reports_the_kilometres_each_mode_carried(self):
        found = routes_search.route(self.world_map, ["a1"], ["a2"], {"cart", "road"})
        self.assertAlmostEqual(sum(found["inputs"]["km_by_mode"].values()), found["km"])

    def test_carriage_rates_give_the_level_team_days_and_carrier_days_per_tonne_km(self):
        rates = api.carriage_rates(["cart", "road"])
        for mode, entry in rates.items():
            self.assertGreaterEqual(entry["team_days_per_tonne_km"], 1.0 / entry["tonne_km_per_team_day"] - 1e-12, mode)
            for kind, name, count in entry["carriers"]:
                days = {(each[0], each[1]): each[2] for each in entry["carrier_days_per_tonne_km"]}[(kind, name)]
                self.assertAlmostEqual(days, count * entry["team_days_per_tonne_km"], msg=mode)


if __name__ == "__main__":
    unittest.main()
