"""Complaint 473: a newcomer prices a site at the rent its own use would pay there (`land_market.use_rent_per_hectare`),
not at the tile's mean rent, which a use that earns a great deal from a hectare bids up."""

QUICK_TOPIC = True

import unittest

from sim.economy import entrant_rent, entry_year
from sim.economy.economy import Economy
from sim.economy.entry import UnmetDemand
from sim.economy.land_market import LandDemand, clear_land
from sim.economy.location import entry_siting
from sim.economy.record import EconomyRecord
from sim.tests import economy_fixture as fixture

GRAIN_VALUE = 100.0         # output value a hectare of the grain use
MINE_VALUE = 10000.0        # output value a hectare of the mine use
LAND_PER_RUN = 2.0          # hectare-years a grain run takes


def tile_with_a_mine():
    """The cleared land of a short tile worked by a grain use and a mine."""
    demands = [LandDemand("grain", "t", 90.0, GRAIN_VALUE, 40.0), LandDemand("mine", "t", 10.0, MINE_VALUE, 40.0)]
    return clear_land({"t": 100.0}, demands)


def grain_value_a_hectare(economy):
    view = economy.view()
    price = view.price(fixture.GRAIN, view.area_of(fixture.GRAIN, fixture.FARMS))
    return fixture.recipes()[fixture.FARM].outputs[fixture.GRAIN] * price / LAND_PER_RUN


class EntrantRentRuleTests(unittest.TestCase):
    def test_a_grain_entrant_on_a_tile_with_a_mine_pays_its_own_uses_rent_not_the_tile_mean(self):
        result = tile_with_a_mine()
        tile_rent = result.rent_per_hectare_by_tile["t"]
        rent = entrant_rent.rent_per_run(result.rent_per_hectare_by_tile, result.mean_value_by_tile, "t",
                                         LAND_PER_RUN, GRAIN_VALUE * LAND_PER_RUN)
        mean_value = result.mean_value_by_tile["t"]
        self.assertGreater(tile_rent, 0.0)
        self.assertAlmostEqual(rent, tile_rent * GRAIN_VALUE / mean_value * LAND_PER_RUN)
        self.assertLess(rent, tile_rent * LAND_PER_RUN)

    def test_an_entrant_whose_use_is_at_the_tile_mean_pays_the_tile_rent(self):
        result = tile_with_a_mine()
        mean_value = result.mean_value_by_tile["t"]
        rent = entrant_rent.rent_per_run(result.rent_per_hectare_by_tile, result.mean_value_by_tile, "t",
                                         LAND_PER_RUN, mean_value * LAND_PER_RUN)
        self.assertAlmostEqual(rent, result.rent_per_hectare_by_tile["t"] * LAND_PER_RUN)

    def test_a_recipe_that_takes_no_land_pays_no_rent(self):
        result = tile_with_a_mine()
        self.assertEqual(entrant_rent.rent_per_run(result.rent_per_hectare_by_tile, result.mean_value_by_tile, "t", 0.0, 5.0), 0.0)

    def test_a_tile_with_no_known_mean_charges_the_tile_rent(self):
        self.assertEqual(entrant_rent.rent_per_run({"t": 7.0}, {}, "t", LAND_PER_RUN, 50.0), 7.0 * LAND_PER_RUN)

    def test_the_site_rent_reads_the_entrants_expected_revenue_from_the_view(self):
        setup = fixture.small_setup(land_per_run={fixture.FARM: LAND_PER_RUN})
        economy = Economy(setup)
        record = economy.record
        grain_value = grain_value_a_hectare(economy)
        record.land_rent = {fixture.FARMS: 50.0}
        record.land_mean_value = {fixture.FARMS: grain_value}
        self.assertAlmostEqual(entrant_rent.site_rent_per_run(setup, record, economy.view(), fixture.FARM, fixture.FARMS),
                               50.0 * LAND_PER_RUN)
        record.land_mean_value = {fixture.FARMS: 4.0 * grain_value}
        self.assertAlmostEqual(entrant_rent.site_rent_per_run(setup, record, economy.view(), fixture.FARM, fixture.FARMS),
                               50.0 * LAND_PER_RUN / 4.0)

    def test_the_record_keeps_the_mean_values_through_a_save(self):
        record = Economy(fixture.small_setup()).record
        record.land_mean_value = {"t": 12.5}
        self.assertEqual(EconomyRecord.from_record(record.to_record()).land_mean_value, {"t": 12.5})


class EntrySitingByOwnRentTests(unittest.TestCase):
    def sited_tile(self, mean_value_by_tile):
        setup = fixture.small_setup(land_per_run={fixture.FARM: LAND_PER_RUN})
        economy = Economy(setup)
        record = economy.record
        # farms: a high tile rent that a mine bids up; hills: a lower rent set by uses like grain
        record.land_rent = {fixture.FARMS: 400.0, fixture.HILLS: 100.0, fixture.TOWN: 1e6}
        grain = grain_value_a_hectare(economy)
        record.land_mean_value = {**mean_value_by_tile(grain), fixture.TOWN: grain}    # the town's rent is dear whatever the use
        area = economy.area_map.areas(fixture.GRAIN)[0]
        siting = entry_siting(setup, record, economy.view(), economy.area_map, entry_year._carriage(setup))
        return siting(fixture.FARM, UnmetDemand(fixture.GRAIN, area.area_id, area.anchor_tile, 1000.0), 1.0)[0]

    def test_a_grain_entrant_is_sited_where_its_own_use_pays_the_least_rent(self):
        self.assertEqual(self.sited_tile(lambda grain: {fixture.FARMS: 1000.0 * grain, fixture.HILLS: grain}), fixture.FARMS)

    def test_with_every_use_at_the_tile_mean_the_lower_tile_rent_wins(self):
        self.assertEqual(self.sited_tile(lambda grain: {fixture.FARMS: grain, fixture.HILLS: grain}), fixture.HILLS)


if __name__ == "__main__":
    unittest.main()
