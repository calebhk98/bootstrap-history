"""Complaint 473: the opening puts each processor of a fixed-site good beside that good's supply, in a market area that
makes it. `location_inputs.fixed_inputs` names the processors and `location_inputs.place_oriented` places them, each called
on a record, an area map and a carriage table written out here: the only ore is dug on the hills."""
import dataclasses
import types
import unittest

from sim.economy import location_inputs, sites
from sim.economy.producers import Producer
from sim.economy.types import SiteLimit
from sim.tests import economy_fixture as fixture

QUICK_TOPIC = True

DISTANCE = {frozenset((fixture.TOWN, fixture.FARMS)): 1.0, frozenset((fixture.FARMS, fixture.HILLS)): 1.0,
            frozenset((fixture.TOWN, fixture.HILLS)): 2.0}
PEOPLE = {fixture.TOWN: 1000.0, fixture.FARMS: 1000.0, fixture.HILLS: 1000.0}
ORE_RUNS = 100.0


def recipes_with_ore_on_the_hills():
    recipes = fixture.recipes()
    recipes[fixture.MINE] = dataclasses.replace(recipes[fixture.MINE], site_bound=True)
    return recipes


class Carriage:
    def cost_per_tonne(self, source, destination):
        return 0.0 if source == destination else DISTANCE[frozenset((source, destination))]


class AreaMap:
    """Ore is one market area on the hills and another elsewhere; every other good has one area."""

    def __init__(self, ore_area_of_tile):
        self.ore_area_of_tile = ore_area_of_tile

    def area_of(self, good, tile):
        return self.ore_area_of_tile[tile] if good == fixture.ORE else "area:all"


def world(ore_area_of_tile=None):
    recipes = recipes_with_ore_on_the_hills()
    setup = types.SimpleNamespace(
        recipes=recipes, specs=fixture.specs(), opening_population_by_tile=dict(PEOPLE), working_share=0.5,
        working_hours_per_year=2000.0, site_limits=(SiteLimit(fixture.MINE, fixture.HILLS, 1.0e6, 1.0),))
    mine = Producer("producer:dig_ore@hills", "owner", fixture.MINE, fixture.HILLS, ORE_RUNS, expected_sales=ORE_RUNS)
    record = types.SimpleNamespace(producers={mine.agent_id: mine})
    area_map = AreaMap(ore_area_of_tile or {tile: "area:all" for tile in PEOPLE})
    anchor = types.SimpleNamespace(area_id="area:all", anchor_tile=fixture.TOWN)
    return setup, record, area_map, [(anchor, 5.0)]


class OpeningSmeltersBesideOreTests(unittest.TestCase):
    def test_the_smelter_is_a_processor_of_a_fixed_site_good(self):
        recipes = recipes_with_ore_on_the_hills()
        by_limits = sites.limits_by_recipe((SiteLimit(fixture.MINE, fixture.HILLS, 1.0e6, 1.0),))
        fixed = location_inputs.fixed_inputs(recipes[fixture.SMELT], {fixture.ORE: fixture.MINE}, recipes, by_limits)
        self.assertEqual(fixed, {fixture.ORE: fixture.MINE})

    def test_a_smelter_sits_at_its_ore_when_the_ore_is_what_it_carries(self):
        setup, record, area_map, shares = world()
        placed = location_inputs.place_oriented(setup, record, area_map, Carriage(), setup.recipes[fixture.SMELT],
                                                {fixture.ORE: fixture.MINE}, shares, sorted(PEOPLE))
        self.assertEqual(list(placed), [fixture.HILLS])

    def test_a_processor_of_a_fixed_site_good_sits_in_a_market_area_that_makes_it(self):
        areas = {fixture.TOWN: "area:town", fixture.FARMS: "area:farms", fixture.HILLS: "area:hills"}
        setup, record, area_map, shares = world(areas)
        placed = location_inputs.place_oriented(setup, record, area_map, Carriage(), setup.recipes[fixture.SMELT],
                                                {fixture.ORE: fixture.MINE}, shares, sorted(PEOPLE))
        self.assertTrue(placed)
        self.assertEqual({area_map.area_of(fixture.ORE, tile) for tile in placed}, {"area:hills"})

    def test_a_smelter_takes_no_more_runs_on_a_tile_than_the_hands_there_can_spare(self):
        setup, record, area_map, _shares = world()
        setup.opening_population_by_tile[fixture.HILLS] = 100.0
        shares = [(types.SimpleNamespace(area_id="area:all", anchor_tile=fixture.TOWN), 1.0e6)]
        placed = location_inputs.place_oriented(setup, record, area_map, Carriage(), setup.recipes[fixture.SMELT],
                                                {fixture.ORE: fixture.MINE}, shares, sorted(PEOPLE))
        mine_hours = ORE_RUNS * sum(setup.recipes[fixture.MINE].labour_hours.values())
        smelter_hours_per_run = sum(setup.recipes[fixture.SMELT].labour_hours.values())
        spare_runs = (100.0 * setup.working_share * setup.working_hours_per_year - mine_hours) / smelter_hours_per_run
        self.assertAlmostEqual(placed[fixture.HILLS], spare_runs)


if __name__ == "__main__":
    unittest.main()
