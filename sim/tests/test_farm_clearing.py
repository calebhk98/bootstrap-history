"""The farmed area grows toward the arable ceiling, best ground first, paid for in labour and driven by food scarcity;
land rent reads the same ladder.

Rules, each called on inputs the test builds:

1. `land.territory_cropland` and `land.ladder_quality`: the ladder is best ground first, sums to the ceiling, and the
   mean quality falls as worse ground is brought in.
2. `labour_allocation.hours_spent_clearing`, `cleared_hectares`, `quality_of_area`: clearing is paid in the hands beyond
   what the farm can crop, never passes the arable ceiling, and the new ground is no better than the old.
3. `land.margin_outcome_for_civilization` and `prices.band_farmed_hectares`: rent reads the farmed area.

The years of clearing in a game, the save round trip and the price tables following the area are
`test_farm_clearing_scenario`."""
QUICK_TOPIC = True

import json
import os
import unittest

from sim.geography.api import crop_site, tiles_held
from sim.geography.food_crops import CropSite
from sim.world import demography
from sim.labour import labour_allocation
from sim.world import agriculture, agriculture_labour, farming_technique, land

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOURS = labour_allocation.HOURS_PER_FARM_WORKER_YEAR
TECHNIQUE = farming_technique.DEFAULT_TECHNIQUE

# tile -> (cropped hectares, yield factor); the third tile is unfarmable
SITES = {
    "plain": CropSite(1200.0, 1000.0, 1.4),
    "hills": CropSite(600.0, 500.0, 0.9),
    "marsh": CropSite(900.0, 800.0, 0.5),
    "dune": CropSite(300.0, 250.0, 0.0),
}


class LadderTests(unittest.TestCase):
    def setUp(self):
        self.territory = land.territory_cropland(SITES)

    def test_ladder_is_best_ground_first(self):
        fertilities = [fertility for fertility, _hectares in self.territory.ladder]
        self.assertEqual(fertilities, sorted(fertilities, reverse=True))

    def test_ladder_sums_to_the_ceiling_and_leaves_out_unfarmable_ground(self):
        self.assertAlmostEqual(sum(hectares for _fertility, hectares in self.territory.ladder),
                               self.territory.cropped_hectares, places=6)
        self.assertAlmostEqual(self.territory.cropped_hectares, 1000.0 + 500.0 + 800.0, places=6)
        self.assertTrue(all(fertility > 0.0 for fertility, _hectares in self.territory.ladder))

    def test_quality_falls_as_worse_ground_is_brought_in(self):
        ceiling = self.territory.cropped_hectares
        qualities = [land.ladder_quality(self.territory.ladder, ceiling * share) for share in (0.05, 0.2, 0.5, 1.0)]
        self.assertEqual(qualities, sorted(qualities, reverse=True))
        self.assertAlmostEqual(qualities[-1], self.territory.mean_yield_factor, places=9)

    def test_the_first_hectares_are_the_best_ground(self):
        self.assertAlmostEqual(land.ladder_quality(self.territory.ladder, 500.0), 1.4, places=9)

    def test_ground_with_no_farmable_tile_is_empty_not_an_error(self):
        territory = land.territory_cropland({"dune": SITES["dune"]})
        self.assertEqual(territory.ladder, [])
        self.assertEqual(territory.cropped_hectares, 0.0)


class ClearingRuleTests(unittest.TestCase):
    def test_labour_cost_is_a_declared_labelled_parameter(self):
        self.assertGreater(agriculture.CLEARING_LABOUR_HOURS_PER_HECTARE, 0.0)

    def test_hands_the_farm_can_crop_do_not_clear(self):
        crop_limit_fte = 1000.0 / agriculture.hectares_cropped_per_farm_worker(TECHNIQUE.crop, TECHNIQUE.toolkit)
        self.assertEqual(labour_allocation.hours_spent_clearing(crop_limit_fte, 1000.0, TECHNIQUE), 0.0)
        self.assertEqual(labour_allocation.hours_spent_clearing(0.5 * crop_limit_fte, 1000.0, TECHNIQUE), 0.0)

    def test_hands_beyond_what_the_farm_can_crop_spend_their_year_clearing(self):
        crop_limit_fte = 1000.0 / agriculture.hectares_cropped_per_farm_worker(TECHNIQUE.crop, TECHNIQUE.toolkit)
        hours = labour_allocation.hours_spent_clearing(crop_limit_fte + 7.0, 1000.0, TECHNIQUE)
        self.assertAlmostEqual(hours, 7.0 * HOURS)

    def test_clearing_is_paid_in_the_hours_it_takes(self):
        hours = 10.0 * agriculture.CLEARING_LABOUR_HOURS_PER_HECTARE
        self.assertAlmostEqual(labour_allocation.cleared_hectares(hours, 1000.0, 5000.0), 10.0)

    def test_area_never_passes_the_arable_ceiling(self):
        cleared = labour_allocation.cleared_hectares(1e12, 1000.0, 2300.0)
        self.assertAlmostEqual(cleared, 1300.0)
        self.assertEqual(labour_allocation.cleared_hectares(1e12, 2300.0, 2300.0), 0.0)
        self.assertEqual(labour_allocation.cleared_hectares(1e12, 2400.0, 2300.0), 0.0)

    def test_without_a_ceiling_there_is_nothing_to_clear(self):
        self.assertEqual(labour_allocation.cleared_hectares(1e12, 1000.0, None), 0.0)

    def test_new_ground_is_no_better_than_the_ground_already_farmed(self):
        ladder = land.territory_cropland(SITES).ladder
        before = labour_allocation.quality_of_area(ladder, 800.0)
        after = labour_allocation.quality_of_area(ladder, 800.0 + labour_allocation.cleared_hectares(1e12, 800.0, 2300.0))
        self.assertLess(after, before)
        self.assertAlmostEqual(after, land.ladder_quality(ladder, 2300.0), places=9)

    def test_without_a_ladder_quality_is_the_reference_field(self):
        self.assertEqual(labour_allocation.quality_of_area([], 500.0), 1.0)


class OpeningAreaTests(unittest.TestCase):
    """The ground cleared at the opening nets as much food after seed as the population's reference-soil area."""
    crop = TECHNIQUE.crop

    def _net_kg(self, ladder, hectares):
        gross_per_hectare = (self.crop.planting_material_kg_per_ha * self.crop.fold_return_on_planting_material
                             * TECHNIQUE.toolkit.ploughing_yield_multiplier
                             * TECHNIQUE.rotation.soil_fertility_yield_multiplier)
        total = 0.0
        for fertility, parcel_hectares in ladder:
            step = min(parcel_hectares, hectares)
            total += step * (gross_per_hectare * fertility - self.crop.planting_material_kg_per_ha)
            hectares -= step
        return total

    def test_reference_ground_needs_the_reference_hectares(self):
        sized = agriculture_labour.hectares_netting_reference_food([(1.0, 9000.0)], 1000.0, TECHNIQUE.crop,
                                                                   None, TECHNIQUE.rotation, TECHNIQUE.toolkit)
        self.assertAlmostEqual(sized, 1000.0, places=6)

    def test_poorer_ground_takes_more_hectares_than_the_yield_ratio_because_seed_is_sown_on_all(self):
        ladder = [(0.6, 100000.0)]
        sized = agriculture_labour.hectares_netting_reference_food(ladder, 1000.0, TECHNIQUE.crop,
                                                                   None, TECHNIQUE.rotation, TECHNIQUE.toolkit)
        self.assertGreater(sized, 1000.0 / 0.6)
        reference_net = self._net_kg([(1.0, 1000.0)], 1000.0)
        self.assertAlmostEqual(self._net_kg(ladder, sized), reference_net, delta=reference_net * 1e-9)

    def test_ground_that_does_not_cover_its_seed_is_left_out_and_the_ground_held_caps_it(self):
        sized = agriculture_labour.hectares_netting_reference_food([(1.4, 100.0), (0.1, 1e6)], 1000.0,
                                                                   TECHNIQUE.crop, None, TECHNIQUE.rotation,
                                                                   TECHNIQUE.toolkit)
        self.assertAlmostEqual(sized, 100.0, places=9)
        self.assertEqual(agriculture_labour.hectares_netting_reference_food([], 1000.0), 0.0)

    def test_a_territory_with_no_arable_ground_opens_no_farm(self):
        # An empty ladder is ground known to be absent, not ground unknown: no hectares are invented.
        self.assertEqual(agriculture_labour.farmland_for_population(1.0e6, ladder=[]).hectares, 0.0)
        self.assertGreater(agriculture_labour.farmland_for_population(1.0e6, ladder=None).hectares, 0.0)

    def test_a_territory_of_zero_fertility_opens_no_farm(self):
        self.assertEqual(agriculture_labour.farmland_for_population(1.0e6, ladder=[(0.0, 1e6)]).hectares, 0.0)

    def test_the_norse_opening_ground_nets_what_its_people_eat(self):
        civ = json.load(open(os.path.join(ROOT, "data", "civilizations", "norse_900ad.json"), encoding="utf-8"))
        share = 1.0 - agriculture.DEFAULT_ROTATION.fallow_share_of_holding
        ladder = land.territory_cropland({tile: crop_site(tile, share) for tile in tiles_held(civ)}).ladder
        people = demography.Population.stationary(float(civ["population"]), seed=1)
        adult_equivalents = (people.children * demography.CHILD_CALORIE_EQUIVALENT + people.working_age
                             + people.elderly * demography.ELDERLY_CALORIE_EQUIVALENT)
        reference = agriculture.farmland_for_population(adult_equivalents).hectares
        hectares = agriculture.farmland_for_population(adult_equivalents, ladder=ladder).hectares
        self.assertGreater(hectares, reference)
        self.assertAlmostEqual(self._net_kg(ladder, hectares), self._net_kg([(1.0, reference)], reference),
                               delta=self._net_kg([(1.0, reference)], reference) * 1e-6)
        workers = hectares / agriculture.hectares_cropped_per_farm_worker(TECHNIQUE.crop, TECHNIQUE.toolkit)
        self.assertLess(workers, people.working_age)


class RentReadsTheFarmedAreaTests(unittest.TestCase):
    def test_margin_is_the_last_ground_the_farm_covers(self):
        civ_id = "han_china_100ad"
        ceiling = land.margin_outcome_for_civilization(civ_id, farmed_hectares=1e12)
        total = sum(a.arable_hectares_supplied for a in ceiling.allocations)
        small = land.margin_outcome_for_civilization(civ_id, farmed_hectares=total * 0.02)
        large = land.margin_outcome_for_civilization(civ_id, farmed_hectares=total * 0.6)
        self.assertGreater(small.margin_fertility_quality_multiplier, large.margin_fertility_quality_multiplier)
        self.assertAlmostEqual(sum(a.arable_hectares_supplied for a in large.allocations), total * 0.6, delta=total * 0.01)

    def test_nearby_areas_share_one_solve(self):
        from sim.engine import prices
        self.assertEqual(prices.band_farmed_hectares(1000.0), prices.band_farmed_hectares(1001.0))
        self.assertNotEqual(prices.band_farmed_hectares(1000.0), prices.band_farmed_hectares(2000.0))


if __name__ == "__main__":
    unittest.main()
