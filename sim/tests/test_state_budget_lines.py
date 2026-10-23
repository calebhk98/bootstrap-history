"""Complaint 640: what a state maintains beyond its army and officials (roads, public buildings, a court, a dole, a navy), each
line built from a stand-in world that answers only what the line reads. No game."""

QUICK_TOPIC = True

import types
import unittest

from sim.agents import budget_lines
from sim.agents.tuning_spending import (COAST_KM_PER_SHIP, COURT_RETAINERS_PER_OFFICIAL, DOLE_SHARE_OF_URBAN_PEOPLE,
                                        MAX_STATE_SHARE_OF_TRADE, ROAD_UPKEEP_PERSON_YEARS_PER_KM)

WAGE = {"labourer": 10.0, "mason": 20.0, "sailor": 15.0, "trireme_wright": 25.0}


class StubWorld:
    def __init__(self, road_km=100.0, coast_km=500.0, urban=10000.0, fleet=(), levers=None, price=2.0, national=1.0e9):
        self._territory = types.SimpleNamespace(road_km=road_km, coast_km=coast_km)
        self.urban, self.fleet, self.levers, self.price, self.national = urban, list(fleet), levers or {}, price, national

    def territory(self):
        return self._territory

    def urban_population(self):
        return self.urban

    def national_people(self, trade):
        return self.national

    def pay_per_person_year(self, trade):
        return WAGE[trade]

    def subsistence_kg_per_person_year(self):
        return 200.0

    def commodity_of(self, material):
        return material

    def material_cost(self, material, tonnes):
        return None if self.price is None else tonnes * self.price

    def government(self):
        return types.SimpleNamespace(record=types.SimpleNamespace(levers=self.levers))

    def fleet_goods(self):
        return self.fleet

    def trade_exists(self, trade):
        return True


def ship(material="trireme", life=20.0, held=0.0, crew=None):
    return {"material": material, "life": life, "held": held, "crew": crew or {"sailor": 100.0}}


class Roads(unittest.TestCase):
    def test_roads_are_labourers_in_proportion_to_the_road_length_held(self):
        line = budget_lines.roads_line(StubWorld(road_km=100.0))[0]
        self.assertAlmostEqual(line.labour["labourer"], 100.0 * ROAD_UPKEEP_PERSON_YEARS_PER_KM)
        self.assertAlmostEqual(line.wages, line.labour["labourer"] * WAGE["labourer"])
        self.assertGreater(budget_lines.roads_line(StubWorld(road_km=200.0))[0].money, line.money)

    def test_a_state_with_no_road_keeps_no_roads(self):
        self.assertEqual(budget_lines.roads_line(StubWorld(road_km=0.0)), [])


class PublicBuildings(unittest.TestCase):
    def test_public_buildings_are_masons_work_and_grow_with_the_town_dwellers(self):
        small = budget_lines.public_buildings_line(StubWorld(urban=10000.0))[0]
        large = budget_lines.public_buildings_line(StubWorld(urban=20000.0))[0]
        self.assertIn("mason", small.labour)
        self.assertAlmostEqual(large.money, 2.0 * small.money)

    def test_no_town_dwellers_keep_no_buildings(self):
        self.assertEqual(budget_lines.public_buildings_line(StubWorld(urban=0.0)), [])


class Court(unittest.TestCase):
    def test_a_court_keeps_retainers_per_official_and_none_without_officials(self):
        line = budget_lines.court_line(StubWorld(), 50.0)[0]
        self.assertAlmostEqual(line.labour["labourer"], 50.0 * COURT_RETAINERS_PER_OFFICIAL)
        self.assertEqual(line.kind, "office")
        self.assertEqual(budget_lines.court_line(StubWorld(), 0.0), [])


class Dole(unittest.TestCase):
    def test_the_dole_is_grain_for_a_share_of_the_town_poor_at_the_market_price(self):
        line = budget_lines.dole_line(StubWorld(urban=10000.0))[0]
        tonnes = 10000.0 * DOLE_SHARE_OF_URBAN_PEOPLE * 200.0 / 1000.0
        self.assertAlmostEqual(line.materials[budget_lines.DOLE_MATERIAL], tonnes)
        self.assertAlmostEqual(line.material_cost, tonnes * 2.0)
        self.assertEqual(line.labour, {})

    def test_a_larger_town_population_feeds_more_of_its_poor(self):
        self.assertAlmostEqual(budget_lines.dole_line(StubWorld(urban=20000.0))[0].material_cost,
                               2.0 * budget_lines.dole_line(StubWorld(urban=10000.0))[0].material_cost)

    def test_grain_nobody_sells_is_unbuyable_not_free(self):
        line = budget_lines.dole_line(StubWorld(price=None))[0]
        self.assertEqual(line.materials, {})
        self.assertGreater(line.unbuyable[budget_lines.DOLE_MATERIAL], 0.0)

    def test_no_town_poor_no_dole(self):
        self.assertEqual(budget_lines.dole_line(StubWorld(urban=0.0)), [])


class Navy(unittest.TestCase):
    def test_a_navy_is_manned_by_sailors_for_the_ships_the_coast_asks(self):
        line = budget_lines.navy_line(StubWorld(coast_km=500.0, fleet=[ship()]))[0]
        self.assertAlmostEqual(line.labour["sailor"], 500.0 / COAST_KM_PER_SHIP * 100.0)

    def test_the_lever_sets_the_fleet_instead_of_the_coast(self):
        line = budget_lines.navy_line(StubWorld(coast_km=500.0, fleet=[ship()], levers={"navy": 2.0}))[0]
        self.assertAlmostEqual(line.labour["sailor"], 200.0)

    def test_no_coast_or_no_ship_type_keeps_no_navy(self):
        self.assertEqual(budget_lines.navy_line(StubWorld(coast_km=0.0, fleet=[ship()])), [])
        self.assertEqual(budget_lines.navy_line(StubWorld(coast_km=500.0, fleet=[])), [])

    def test_ships_already_held_cover_the_wear_so_only_the_missing_are_bought(self):
        none_held = budget_lines.navy_line(StubWorld(coast_km=500.0, fleet=[ship(held=0.0)]))[0]
        many_held = budget_lines.navy_line(StubWorld(coast_km=500.0, fleet=[ship(held=1000.0)]))[0]
        self.assertGreater(none_held.material_cost, 0.0)
        self.assertEqual(many_held.material_cost, 0.0)

    def test_the_ship_type_cheaper_to_keep_is_chosen(self):
        cheap = ship(material="cheap", crew={"sailor": 10.0})
        dear = ship(material="dear", crew={"sailor": 100.0})
        line = budget_lines.navy_line(StubWorld(coast_km=500.0, fleet=[dear, cheap]))[0]
        self.assertAlmostEqual(line.labour["sailor"], 5.0 * 10.0)


class StateShareOfATrade(unittest.TestCase):
    def test_a_line_never_takes_more_of_a_trade_than_the_state_share_of_its_people(self):
        world = StubWorld(urban=1.0e9, national=1000.0)
        line = budget_lines.public_buildings_line(world)[0]
        self.assertAlmostEqual(line.labour["mason"], MAX_STATE_SHARE_OF_TRADE * 1000.0)

    def test_unskilled_labour_is_not_held_to_that_share(self):
        line = budget_lines.paid(StubWorld(national=10.0), "x", "requisition", {"labourer": 500.0})
        self.assertEqual(line.labour["labourer"], 500.0)


if __name__ == "__main__":
    unittest.main()
