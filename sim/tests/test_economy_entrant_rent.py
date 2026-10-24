"""Complaint 473: a newcomer prices a site at the rent its own use would pay there (`land_market.use_rent_per_hectare`),
not at the tile's mean rent, which a use that earns a great deal from a hectare bids up."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import entrant_rent, location
from sim.economy.land_market import LandDemand, clear_land
from sim.tests import economy_fixture as fixture

GRAIN_VALUE = 100.0         # output value a hectare of the grain use
MINE_VALUE = 10000.0        # output value a hectare of the mine use
LAND_PER_RUN = 2.0          # hectare-years a grain run takes


def tile_with_a_mine():
    """The cleared land of a short tile worked by a grain use and a mine."""
    demands = [LandDemand("grain", "t", 90.0, GRAIN_VALUE, 40.0), LandDemand("mine", "t", 10.0, MINE_VALUE, 40.0)]
    return clear_land({"t": 100.0}, demands)


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
        recipe = fixture.recipes()[fixture.FARM]
        setup = types.SimpleNamespace(recipes={fixture.FARM: recipe}, land_per_run={fixture.FARM: LAND_PER_RUN})
        grain_value = recipe.outputs[fixture.GRAIN] * 0.1 / LAND_PER_RUN
        record = types.SimpleNamespace(land_rent={fixture.FARMS: 50.0}, land_mean_value={fixture.FARMS: grain_value})
        with mock.patch.object(entrant_rent, "expected_output_prices", lambda producer, _recipe, _view: {fixture.GRAIN: 0.1}):
            self.assertAlmostEqual(entrant_rent.site_rent_per_run(setup, record, None, fixture.FARM, fixture.FARMS),
                                   50.0 * LAND_PER_RUN)
            record.land_mean_value = {fixture.FARMS: 4.0 * grain_value}
            self.assertAlmostEqual(entrant_rent.site_rent_per_run(setup, record, None, fixture.FARM, fixture.FARMS),
                                   50.0 * LAND_PER_RUN / 4.0)


class EntrySitingByOwnRentTests(unittest.TestCase):
    def variable_cost_on(self, tile, rent_of_the_entrants_use):
        """The variable cost per run `entry_siting` prices a grain run at on `tile`, the site rent being what the entrant's own use pays."""
        recipe = fixture.recipes()[fixture.FARM]
        setup = types.SimpleNamespace(opening_wages={fixture.LABOURER: 1.0}, yield_factor_by_recipe_tile={}, specs={},
                                      working_hours_per_year=2000.0)
        record = types.SimpleNamespace(workforce=None)
        view = types.SimpleNamespace(wage=lambda trade, area: None)
        with mock.patch.object(location, "site_rent_per_run", lambda *_args: rent_of_the_entrants_use[tile]), \
                mock.patch.object(location, "live_input_prices", lambda *_args: {}), \
                mock.patch.object(location.location_inputs, "input_haul_cost", lambda *_args: 0.0), \
                mock.patch.object(location.labour_state, "people_by_trade", lambda *_args: {}):
            return location._tile_part(setup, record, view, None, recipe, {}, {}, {}, {}, tile)[0]

    def test_a_tiles_run_costs_its_labour_and_the_rent_of_the_entrants_own_use(self):
        labour = fixture.recipes()[fixture.FARM].labour_hours[fixture.LABOURER] * 1.0
        rents = {fixture.FARMS: 80.0, fixture.HILLS: 20.0}
        self.assertAlmostEqual(self.variable_cost_on(fixture.FARMS, rents), labour + 80.0)
        self.assertAlmostEqual(self.variable_cost_on(fixture.HILLS, rents), labour + 20.0)


if __name__ == "__main__":
    unittest.main()
