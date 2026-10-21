"""Complaint 640: real output per head divides a country's output by that country's people, so the volumes and the
opening basket it is measured on are that country's own. Built inputs, the rules called directly: a basket holding
home and partner-country market volumes is scoped to the country asked for."""
QUICK_TOPIC = True

import types
import unittest

from sim.economy import country_figures

AREAS = {"grain": {"grain_home": {"h1", "h2"}, "grain_far": {"p1"}}, "cloth": {"cloth_all": {"h1", "p1"}}}
OWNERS = {"h1": "home", "h2": "home", "p1": "partner"}


def economy(volumes, basket=None, demand=None, demand_by_country=None):
    areas = {good: [types.SimpleNamespace(area_id=name, tiles=tiles) for name, tiles in by_area.items()]
             for good, by_area in AREAS.items()}
    area_map = types.SimpleNamespace(goods=lambda: list(areas), areas=lambda good: areas[good])
    setup = types.SimpleNamespace(
        tiles=OWNERS, civ_id="home", countries=lambda: ("home", "partner"),
        tiles_of=lambda country: tuple(tile for tile, owner in OWNERS.items() if owner == country))
    record = types.SimpleNamespace(volumes=volumes, opening_basket=basket or {}, opening_demand=demand or {},
                                   opening_demand_by_country=demand_by_country or {})
    return types.SimpleNamespace(setup=setup, record=record, area_map=area_map)


class CountryScopeTests(unittest.TestCase):
    def test_traded_volumes_count_only_the_markets_that_touch_the_countrys_tiles(self):
        built = economy({"grain|grain_home": 10.0, "grain|grain_far": 7.0, "cloth|cloth_all": 3.0})
        self.assertEqual(country_figures.traded_volumes(built, "home"), {"grain": 10.0, "cloth": 3.0})
        self.assertEqual(country_figures.traded_volumes(built, "partner"), {"grain": 7.0, "cloth": 3.0})

    def test_a_home_shock_leaves_the_partner_volumes_out_of_the_home_figure(self):
        calm = country_figures.traded_volumes(economy({"grain|grain_home": 10.0, "grain|grain_far": 7.0}), "home")
        shocked = country_figures.traded_volumes(economy({"grain|grain_home": 5.0, "grain|grain_far": 70.0}), "home")
        self.assertEqual(shocked["grain"] / calm["grain"], 0.5)

    def test_no_country_means_every_market(self):
        built = economy({"grain|grain_home": 10.0, "grain|grain_far": 7.0})
        self.assertEqual(country_figures.traded_volumes(built, None), {"grain": 17.0})

    def test_the_opening_basket_of_a_country_is_the_supplied_part_in_proportion_to_its_demand(self):
        built = economy({}, basket={"grain": 50.0, "salt": 5.0}, demand={"grain": 100.0, "salt": 5.0},
                        demand_by_country={"home": {"grain": 60.0, "salt": 5.0}, "partner": {"grain": 40.0}})
        self.assertEqual(country_figures.opening_basket(built, "home"), {"grain": 30.0, "salt": 5.0})
        self.assertEqual(country_figures.opening_basket(built, "partner"), {"grain": 20.0})
        self.assertEqual(country_figures.opening_basket(built, None), {"grain": 50.0, "salt": 5.0})


if __name__ == "__main__":
    unittest.main()
