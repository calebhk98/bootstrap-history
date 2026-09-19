"""Regression tests for sim/world/land.py.

Written as unittest.TestCase classes, like sim/tests/test_deposits.py and
sim/tests/test_agriculture.py: this module has no dependency on sim/engine/
or any other sim/world/ module (see land.py's own STANDALONE section), so
importing sim/tests/harness.py would pull in the whole engine for no
reason. sim/tests/__main__.py's own _run_topic already runs both styles
identically - this file's module name for that registration is
sim.tests.test_land.

These checks are ORDERINGS and STRUCTURAL PROPERTIES, not particular
numbers - see sim/tests/test_deposits.py's own ExtractionCostMechanicsTests
docstring for the same reasoning applied to a sibling module: the region
area/arable-fraction/fertility figures in data/world/geography.json are
country-scale approximations, but the DIRECTIONS (better land earns more
rent than worse land; more or better territory raises a civilization's
price; a single homogeneous region earns none) are not in doubt regardless
of any one figure's exact size.
"""
import json
import os
import unittest

from sim.world import land

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


def _real_geography():
    # UPDATE (stakeholder maintainability item 6, the two map systems):
    # several tests below need `land_tiles["region_to_tiles"]` to state
    # their own expectation in TILE ids rather than region names, now that
    # `cultivable_land_for_civilization` resolves a civilization's
    # `home_regions` to tiles - see sim/world/land.py's own module
    # docstring, UPDATE (stakeholder maintainability item 6...) section.
    with open(land.GEOGRAPHY_FILE) as handle:
        return json.load(handle)


def _make_region(name, arable_iugera, fertility_quality_multiplier):
    return land.RegionLand(
        region=name, land_area_km2=arable_iugera, arable_fraction=1.0,
        fertility_quality_multiplier=fertility_quality_multiplier,
        arable_iugera=arable_iugera)


class ReferenceYieldTests(unittest.TestCase):

    def test_quality_one_reproduces_the_reference_hectare_yield(self):
        # 1 iugerum at quality 1.0 should be exactly IUGERUM_HECTARES
        # hectares' worth of REFERENCE_WHEAT_YIELD_KG_PER_HECTARE - the
        # anchor everything else in this module is stated relative to.
        expected = (land.REFERENCE_WHEAT_YIELD_KG_PER_HECTARE
                   * land.IUGERUM_HECTARES)
        self.assertAlmostEqual(
            land.reference_yield_kg_per_iugerum(1.0), expected)

    def test_yield_scales_linearly_with_fertility(self):
        base = land.reference_yield_kg_per_iugerum(1.0)
        self.assertAlmostEqual(
            land.reference_yield_kg_per_iugerum(2.0), base * 2.0)
        self.assertAlmostEqual(
            land.reference_yield_kg_per_iugerum(0.5), base * 0.5)

    def test_a_caller_supplied_reference_overrides_the_module_default(self):
        # sim/solve_prices.py passes the LIVE wheat_kg yield rather than
        # relying on this module's own duplicate - see the module
        # docstring's WHY THE HOURS CONVERSION LIVES IN sim/solve_prices.py
        # section.
        default = land.reference_yield_kg_per_iugerum(1.0)
        overridden = land.reference_yield_kg_per_iugerum(
            1.0, kg_per_hectare_at_quality_1=1000.0)
        self.assertNotAlmostEqual(default, overridden)
        self.assertAlmostEqual(overridden, 1000.0 * land.IUGERUM_HECTARES)


class QuantityDemandedTests(unittest.TestCase):

    def test_scales_linearly_with_population(self):
        one = land.quantity_demanded_kg_grain_equivalent(1_000_000)
        two = land.quantity_demanded_kg_grain_equivalent(2_000_000)
        self.assertAlmostEqual(two, one * 2.0)

    def test_zero_population_demands_nothing(self):
        self.assertEqual(land.quantity_demanded_kg_grain_equivalent(0), 0.0)

    def test_negative_population_is_rejected(self):
        with self.assertRaises(ValueError):
            land.quantity_demanded_kg_grain_equivalent(-1)

    def test_positive_for_any_positive_population(self):
        self.assertGreater(land.quantity_demanded_kg_grain_equivalent(1), 0.0)


class MarginOfCultivationTests(unittest.TestCase):
    """Exercises find_margin_of_cultivation directly against small,
    hand-built region lists - the same style sim/tests/test_deposits.py's
    own MarginalDepositRentTests uses against hand-built deposits, rather
    than against data/world/geography.json's real (and larger, harder to
    reason about by eye) numbers.
    """

    def setUp(self):
        # Three regions of falling fertility, each large enough on its own
        # to matter to the margin at the demand levels these tests use.
        self.best = _make_region("best", arable_iugera=1000.0,
                                 fertility_quality_multiplier=1.5)
        self.middle = _make_region("middle", arable_iugera=1000.0,
                                   fertility_quality_multiplier=1.0)
        self.worst = _make_region("worst", arable_iugera=1000.0,
                                  fertility_quality_multiplier=0.5)
        self.regions = [self.middle, self.worst, self.best]  # deliberately
                                                              # out of order

    def _capacity(self, region_land):
        return (region_land.arable_iugera
                * land.reference_yield_kg_per_iugerum(
                    region_land.fertility_quality_multiplier))

    def test_demand_within_the_best_region_alone_needs_nothing_else(self):
        demand = self._capacity(self.best) * 0.5
        outcome = land.find_margin_of_cultivation(self.regions, demand)
        self.assertEqual(outcome.marginal_region, "best")
        # Only the best region is used - THE SINGLE-REGION-EQUIVALENT CASE:
        # nothing better than the margin is in use, so rent is zero even
        # though worse land exists elsewhere in the list.
        self.assertEqual(outcome.price_kg_grain_equivalent_per_iugerum, 0.0)
        for allocation in outcome.allocations:
            if allocation.region_land.region != "best":
                self.assertEqual(allocation.arable_iugera_supplied, 0.0)

    def test_demand_reaching_the_middle_region_gives_the_best_region_rent(self):
        demand = self._capacity(self.best) + self._capacity(self.middle) * 0.5
        outcome = land.find_margin_of_cultivation(self.regions, demand)
        self.assertEqual(outcome.marginal_region, "middle")
        by_region = {a.region_land.region: a for a in outcome.allocations}
        self.assertEqual(by_region["middle"].rent_kg_grain_equivalent_per_iugerum, 0.0)
        self.assertGreater(by_region["best"].rent_kg_grain_equivalent_per_iugerum, 0.0)
        self.assertEqual(by_region["worst"].arable_iugera_supplied, 0.0)

    def test_better_land_earns_more_rent_than_land_closer_to_the_margin(self):
        # Push the margin down to worst, so best, middle and worst are all
        # at least partly in play, and check the ORDERING of rent, not any
        # particular number.
        demand = (self._capacity(self.best) + self._capacity(self.middle)
                 + self._capacity(self.worst) * 0.5)
        outcome = land.find_margin_of_cultivation(self.regions, demand)
        self.assertEqual(outcome.marginal_region, "worst")
        by_region = {a.region_land.region: a for a in outcome.allocations}
        self.assertGreater(
            by_region["best"].rent_kg_grain_equivalent_per_iugerum,
            by_region["middle"].rent_kg_grain_equivalent_per_iugerum)
        self.assertGreater(
            by_region["middle"].rent_kg_grain_equivalent_per_iugerum, 0.0)
        self.assertEqual(
            by_region["worst"].rent_kg_grain_equivalent_per_iugerum, 0.0)

    def test_a_single_homogeneous_region_always_prices_at_zero(self):
        # The degenerate case the module docstring names explicitly: no
        # differential rent without at least two regions of different
        # quality to compare, regardless of how much of the one region is
        # actually used.
        for fraction in (0.1, 0.5, 0.99):
            outcome = land.find_margin_of_cultivation(
                [self.middle], self._capacity(self.middle) * fraction)
            self.assertEqual(outcome.price_kg_grain_equivalent_per_iugerum, 0.0)

    def test_demand_beyond_every_regions_combined_capacity_is_reported_unmet(self):
        total_capacity = sum(self._capacity(r) for r in self.regions)
        outcome = land.find_margin_of_cultivation(
            self.regions, total_capacity * 2.0)
        self.assertGreater(outcome.unmet_demand_kg, 0.0)
        self.assertEqual(outcome.marginal_region, "worst")

    def test_zero_demand_supplies_and_prices_nothing(self):
        outcome = land.find_margin_of_cultivation(self.regions, 0.0)
        self.assertEqual(outcome.price_kg_grain_equivalent_per_iugerum, 0.0)
        self.assertEqual(outcome.quantity_supplied_kg, 0.0)
        for allocation in outcome.allocations:
            self.assertEqual(allocation.arable_iugera_supplied, 0.0)

    def test_negative_demand_is_rejected(self):
        with self.assertRaises(ValueError):
            land.find_margin_of_cultivation(self.regions, -1.0)

    def test_empty_territory_prices_nothing_rather_than_crashing(self):
        outcome = land.find_margin_of_cultivation([], 100.0)
        self.assertEqual(outcome.price_kg_grain_equivalent_per_iugerum, 0.0)
        self.assertIsNone(outcome.marginal_region)
        self.assertGreater(outcome.unmet_demand_kg, 0.0)

    def test_ties_broken_by_name_for_determinism(self):
        tied_a = _make_region("zzz_tied", 1000.0, 1.0)
        tied_b = _make_region("aaa_tied", 1000.0, 1.0)
        first = land.find_margin_of_cultivation([tied_a, tied_b], 10.0)
        second = land.find_margin_of_cultivation([tied_b, tied_a], 10.0)
        self.assertEqual(
            [a.region_land.region for a in first.allocations],
            [a.region_land.region for a in second.allocations])


class RegionDataLoadsCleanlyTests(unittest.TestCase):
    """Checks data/world/geography.json's own `land` blocks, the physical
    facts this module's real callers actually use - see
    sim/tests/test_deposits.py's own CalibrationAgainstBookPricesTests for
    the sibling discipline of reading real project data only in tests,
    never in the module itself.
    """

    def test_every_region_has_a_positive_arable_endowment_or_is_flagged_zero(self):
        region_lands = land.load_region_lands()
        self.assertGreater(len(region_lands), 15)  # the task's own "22
                                                    # regions is the right
                                                    # grain", loosely
        for region_key, region_land in region_lands.items():
            self.assertGreaterEqual(
                region_land.arable_iugera, 0.0,
                "%s: arable_iugera must not be negative" % region_key)
            self.assertGreater(
                region_land.fertility_quality_multiplier, 0.0,
                "%s: fertility_quality_multiplier must be positive "
                "(land.py divides by it nowhere, but a zero or negative "
                "fertility is not a physically meaningful parcel)"
                % region_key)

    def test_italia_is_the_fertility_anchor(self):
        # Not an estimate - see data/world/geography.json's own italia.land
        # entry and this module's own REFERENCE_WHEAT_YIELD_KG_PER_HECTARE
        # declaration for why this one figure is definitional.
        region_lands = land.load_region_lands()
        self.assertEqual(
            region_lands["italia"].fertility_quality_multiplier, 1.0)

    def test_china_has_more_arable_land_than_italia(self):
        # The task's own sanity check: China is a much larger landmass than
        # Italy, and this ordering should survive even generous slack on
        # either region's exact arable_fraction.
        region_lands = land.load_region_lands()
        self.assertGreater(
            region_lands["china"].arable_iugera,
            region_lands["italia"].arable_iugera)

    def test_no_region_land_is_priced_from_a_wished_for_outcome(self):
        # A cheap, structural guard against the CLAUDE.md SS3.1 failure
        # mode: this project's book price for iugerum_land (250 denarii)
        # must not appear anywhere in geography.json's land data, since
        # none of these figures should have been reverse-engineered from
        # it.
        import json
        path = os.path.join(_REPO_ROOT, "data", "world", "geography.json")
        with open(path) as handle:
            raw_text = handle.read()
        geography = json.loads(raw_text)
        for region_key, region_entry in geography["regions"].items():
            if region_key.startswith("_"):
                continue
            land_entry = region_entry.get("land")
            if land_entry is None:
                continue
            self.assertNotEqual(land_entry["fertility_quality_multiplier"], 250.0)
            self.assertNotEqual(land_entry["land_area_km2"], 250.0)


class CivilizationTerritoryTests(unittest.TestCase):
    """cultivable_land_for_civilization and margin_outcome_for_civilization
    against this project's real data/civilizations/*.json files - the
    PER-CIVILISATION, CHANGEABLE requirement the task's own brief names.
    """

    def test_territory_is_the_sum_of_home_regions(self):
        # UPDATE (stakeholder maintainability item 6): `cultivable_land_
        # for_civilization` now returns one parcel per TILE, not per
        # region - see sim/world/land.py's own module docstring. The
        # expectation is restated in tile ids, via the same `region_to_
        # tiles` mapping the function itself resolves `home_regions`
        # through, rather than in the seven region names this test used
        # to name directly.
        geography = _real_geography()
        region_to_tiles = geography["land_tiles"]["region_to_tiles"]
        rome_regions = ["italia", "gaul_germania", "britannia", "hispania",
                        "north_africa", "greece_anatolia", "levant_mesopotamia"]
        expected_tiles = set()
        for region in rome_regions:
            expected_tiles.update(region_to_tiles[region])
        rome_lands = land.cultivable_land_for_civilization("rome_100ad")
        rome_tiles = {rl.region for rl in rome_lands}
        self.assertEqual(rome_tiles, expected_tiles)

    def test_a_civilization_with_more_and_better_territory_scores_higher(self):
        # Not a claim about the FINAL solved price (which also depends on
        # each civilization's own population) - a claim about the
        # underlying territory this module's mechanism is built on: giving
        # a civilization a strictly better and strictly larger set of
        # regions than another must not leave it worse off, all else
        # equal. Constructed directly rather than by picking two real
        # civilizations, so this does not depend on their particular
        # populations lining up conveniently.
        region_lands = land.load_region_lands()
        rich_regions = [region_lands["north_africa"], region_lands["italia"],
                        region_lands["hispania"]]
        poor_region = [region_lands["scandinavia"]]
        same_population = 2_000_000
        demand = land.quantity_demanded_kg_grain_equivalent(same_population)
        rich_outcome = land.find_margin_of_cultivation(rich_regions, demand)
        poor_outcome = land.find_margin_of_cultivation(poor_region, demand)
        self.assertGreaterEqual(
            rich_outcome.price_kg_grain_equivalent_per_iugerum,
            poor_outcome.price_kg_grain_equivalent_per_iugerum)

    def test_conquest_hook_a_civilization_dict_can_be_handed_in_directly(self):
        # See the module docstring's WHAT A LATER CONQUEST MECHANISM WOULD
        # HAVE TO TOUCH section: cultivable_land_for_civilization takes
        # `civilizations` so a caller with an updated, in-memory
        # home_regions list (however it eventually gets updated - out of
        # this module's ownership) is read immediately, with no disk
        # round-trip and no change to this function.
        expanded = {"home_regions": ["italia", "north_africa"]}
        shrunk = {"home_regions": ["italia"]}
        expanded_lands = land.cultivable_land_for_civilization(
            "hypothetical", civilizations={"hypothetical": expanded})
        shrunk_lands = land.cultivable_land_for_civilization(
            "hypothetical", civilizations={"hypothetical": shrunk})
        # UPDATE (stakeholder maintainability item 6): one parcel per
        # TILE now, not per region, so "2" and "1" (one per NAMED region)
        # are no longer the right numbers - italia and north_africa
        # between them resolve to many tiles. The property this test
        # actually cares about (more/better territory means more parcels
        # and more arable land) still holds and is asserted directly.
        self.assertGreater(len(expanded_lands), len(shrunk_lands))
        total_arable = sum(rl.arable_iugera for rl in expanded_lands)
        shrunk_arable = sum(rl.arable_iugera for rl in shrunk_lands)
        self.assertGreater(total_arable, shrunk_arable)

    def test_unknown_civilization_raises_with_the_real_list(self):
        with self.assertRaises(FileNotFoundError):
            land.cultivable_land_for_civilization("atlantis_9999ad")

    def test_a_region_missing_a_land_block_is_skipped_not_fatal(self):
        # UPDATE (stakeholder maintainability item 6): "italia" now
        # resolves to every tile `land_tiles["region_to_tiles"]["italia"]`
        # names, not to one parcel called "italia" - "nowhere_at_all" is
        # still skipped (absent from region_to_tiles too), which is the
        # actual property this test is for.
        geography = _real_geography()
        expected_tiles = set(geography["land_tiles"]["region_to_tiles"]["italia"])
        civilization = {"home_regions": ["italia", "nowhere_at_all"]}
        lands = land.cultivable_land_for_civilization(
            "hypothetical", civilizations={"hypothetical": civilization})
        self.assertEqual({rl.region for rl in lands}, expected_tiles)

    def test_rome_outprices_the_norse(self):
        # The task's own headline check, run against the real solved
        # margin outcome for both real civilizations (not just the raw
        # per-region fertility comparison RegionDataLoadsCleanlyTests
        # already covers) - Rome holds seven regions of varied quality
        # including the two best in the file (north_africa, levant_
        # mesopotamia); the Norse hold exactly one, middling one.
        rome = land.margin_outcome_for_civilization("rome_100ad")
        norse = land.margin_outcome_for_civilization("norse_900ad")
        self.assertGreater(
            rome.price_kg_grain_equivalent_per_iugerum,
            norse.price_kg_grain_equivalent_per_iugerum)

    def test_a_single_home_region_civilization_no_longer_prices_at_zero(self):
        # UPDATE (Complaints/46): this used to assert exactly the opposite
        # - Han China and the Norse both hold exactly one home region, and
        # the OLD, extensive-margin-only mechanism priced both at exactly
        # zero because neither had a worse region of its own to compare
        # against. That was the defect Complaints/46 named: a civilization
        # holding one uniform region has nothing WORSE to earn a
        # differential rent over, regardless of how many people are
        # drawing on it. The INTENSIVE margin (see land.py's own LABOUR
        # INTENSITY section) fixes this without touching the extensive
        # mechanism at all - both civilizations now price above zero
        # purely from their own population pressing on their own land.
        # UPDATE (stakeholder maintainability item 6): "the EXTENSIVE
        # component alone is still exactly zero for a single region" is no
        # longer true, and is no longer the point. `cultivable_land_for_
        # civilization` now resolves ONE home region to MANY tiles (69 for
        # han_china_100ad, 14 for norse_900ad), which very likely have
        # DIFFERENT fertilities from each other - china's own tiles span
        # Gobi desert (near-zero fertility) to Yangtze-basin farmland
        # (above 1.0), for instance. A single-region civilization can
        # therefore now show a real, nonzero EXTENSIVE margin purely from
        # this - which is a BETTER answer than the intensive-only fix this
        # test used to pin (a genuinely varied territory earning genuine
        # differential rent, not just a crowding effect), not a regression
        # of it. What survives from the original claim is the headline:
        # a single-home-region civilization still prices its land above
        # zero, for a reason that no longer depends on there being a
        # second, worse region anywhere else in the file.
        for civilization_id in ("han_china_100ad", "norse_900ad"):
            outcome = land.margin_outcome_for_civilization(civilization_id)
            self.assertGreater(
                outcome.price_kg_grain_equivalent_per_iugerum, 0.0,
                "%s: a single-region civilization should still price its "
                "land above zero" % civilization_id)


# A single, fixed synthetic region used by every test below that needs a
# "solo" civilization's own territory without depending on real geography.
# Declared ONCE, at one fixed set of values, and never varied - land.py's
# own declare() registry rejects the SAME region key re-declared with a
# DIFFERENT value (see sim/constants.py's declare()), so every test that
# needs a different scenario varies the CIVILIZATION (population,
# home_regions) against this same fixed geography instead of the geography
# itself.
# UPDATE (stakeholder maintainability item 6): this fixture now needs a
# `land_tiles` block too, not just `regions` - `cultivable_land_for_
# civilization` reads land_tiles, not regions, since sim/world/land.py's
# own migration (see that module's docstring). One tile, covering exactly
# "solo_test_region"'s own former numbers, keeps every test below that
# uses this fixture numerically IDENTICAL to before the migration - this
# is the SAME scenario the fixture always described, expressed the way
# the post-migration code actually reads it, not a new scenario.
_SOLO_GEOGRAPHY = {
    "regions": {
        "solo_test_region": {
            "land": {
                "land_area_km2": 100000.0,
                "arable_fraction": 0.5,
                "fertility_quality_multiplier": 1.0,
                "conf": "D",
                "source": "sim/tests/test_land.py synthetic fixture",
            }
        }
    },
    "land_tiles": {
        "tiles": {
            "solo_test_tile": {
                "land_area_km2": 100000.0,
                "arable_fraction": 0.5,
                "fertility_quality_multiplier": 1.0,
                "conf": "D",
                "source": "sim/tests/test_land.py synthetic fixture",
            }
        },
        "region_to_tiles": {"solo_test_region": ["solo_test_tile"]},
        "unmapped_tile_count": 0,
    },
}


def _solo_civilization(population):
    return {"home_regions": ["solo_test_region"], "population": population}


class LabourIntensityTests(unittest.TestCase):
    """labour_hours_applied_per_iugerum - the civilization-wide intensity
    figure that feeds the intensive margin, in isolation from any fertility
    or margin-of-cultivation logic.
    """

    def test_scales_linearly_with_population(self):
        one = land.labour_hours_applied_per_iugerum(1_000_000, 500_000.0)
        two = land.labour_hours_applied_per_iugerum(2_000_000, 500_000.0)
        self.assertAlmostEqual(two, one * 2.0)

    def test_scales_inversely_with_arable_land(self):
        small_territory = land.labour_hours_applied_per_iugerum(
            1_000_000, 100_000.0)
        large_territory = land.labour_hours_applied_per_iugerum(
            1_000_000, 1_000_000.0)
        self.assertGreater(small_territory, large_territory)

    def test_zero_land_returns_zero_rather_than_dividing_by_zero(self):
        self.assertEqual(
            land.labour_hours_applied_per_iugerum(1_000_000, 0.0), 0.0)

    def test_negative_population_is_rejected(self):
        with self.assertRaises(ValueError):
            land.labour_hours_applied_per_iugerum(-1, 1000.0)

    def test_negative_land_is_rejected(self):
        with self.assertRaises(ValueError):
            land.labour_hours_applied_per_iugerum(1000, -1.0)


class YieldAtIntensityTests(unittest.TestCase):
    """yield_kg_per_iugerum_at_intensity - the Cobb-Douglas curve this
    module duplicates from sim/world/agriculture.py's own gross_harvest_kg,
    on a per-iugerum basis (see land.py's own LABOUR INTENSITY section).
    """

    def _reference_hours_per_iugerum(self):
        return (land.LAND_REFERENCE_LABOUR_HOURS_PER_HECTARE
               * land.IUGERUM_HECTARES)

    def test_reference_intensity_reproduces_the_flat_reference_yield(self):
        # The calibration promise this whole curve is built around: at
        # exactly the reference intensity, this must equal
        # reference_yield_kg_per_iugerum exactly, for any fertility.
        for fertility in (0.5, 1.0, 1.35):
            expected = land.reference_yield_kg_per_iugerum(fertility)
            actual = land.yield_kg_per_iugerum_at_intensity(
                fertility, self._reference_hours_per_iugerum())
            self.assertAlmostEqual(actual, expected)

    def test_more_labour_raises_yield(self):
        reference_hours = self._reference_hours_per_iugerum()
        low = land.yield_kg_per_iugerum_at_intensity(1.0, reference_hours)
        high = land.yield_kg_per_iugerum_at_intensity(
            1.0, reference_hours * 4.0)
        self.assertGreater(high, low)

    def test_yield_grows_slower_than_labour_diminishing_returns(self):
        # Quadrupling labour must NOT quadruple output - the whole point
        # of LAND_LABOUR_OUTPUT_ELASTICITY < 1.
        reference_hours = self._reference_hours_per_iugerum()
        base = land.yield_kg_per_iugerum_at_intensity(1.0, reference_hours)
        quadrupled = land.yield_kg_per_iugerum_at_intensity(
            1.0, reference_hours * 4.0)
        self.assertLess(quadrupled, base * 4.0)
        self.assertGreater(quadrupled, base)

    def test_zero_labour_yields_nothing(self):
        self.assertEqual(land.yield_kg_per_iugerum_at_intensity(1.0, 0.0), 0.0)

    def test_negative_labour_is_rejected(self):
        with self.assertRaises(ValueError):
            land.yield_kg_per_iugerum_at_intensity(1.0, -1.0)


class IntensiveRentTests(unittest.TestCase):
    """intensive_rent_kg_grain_equivalent_per_iugerum - the Cobb-Douglas
    land share Complaints/46 asked for: rent a SINGLE region earns from
    being crowded, with no other, worse region needed anywhere.
    """

    def test_crowding_a_single_region_raises_its_rent(self):
        low_intensity_rent = land.intensive_rent_kg_grain_equivalent_per_iugerum(
            1.0, 40.0)
        high_intensity_rent = land.intensive_rent_kg_grain_equivalent_per_iugerum(
            1.0, 400.0)
        self.assertGreater(high_intensity_rent, low_intensity_rent)

    def test_better_land_earns_more_even_from_intensive_alone(self):
        # No margin, no comparison region - just fertility, at a FIXED
        # intensity - and the better parcel still earns more.
        worse = land.intensive_rent_kg_grain_equivalent_per_iugerum(0.5, 100.0)
        better = land.intensive_rent_kg_grain_equivalent_per_iugerum(1.5, 100.0)
        self.assertGreater(better, worse)

    def test_zero_labour_earns_no_intensive_rent(self):
        self.assertEqual(
            land.intensive_rent_kg_grain_equivalent_per_iugerum(1.0, 0.0), 0.0)

    def test_never_negative(self):
        for fertility in (0.1, 1.0, 3.0):
            for hours in (0.0, 1.0, 1000.0):
                self.assertGreaterEqual(
                    land.intensive_rent_kg_grain_equivalent_per_iugerum(
                        fertility, hours),
                    0.0)


class CombinedMarginOutcomeTests(unittest.TestCase):
    """margin_outcome_for_civilization - where the extensive margin
    (find_margin_of_cultivation, unchanged) and the intensive margin
    (this task's own addition) are actually added together. Uses the
    fixed _SOLO_GEOGRAPHY fixture so these checks do not depend on real
    geography.json numbers, plus the project's own real civilizations for
    the headline claims the task itself asks to be verified.
    """

    def test_denser_population_on_the_same_single_region_raises_its_price(self):
        sparse = land.margin_outcome_for_civilization(
            "sparse", geography=_SOLO_GEOGRAPHY,
            civilizations={"sparse": _solo_civilization(10_000)})
        dense = land.margin_outcome_for_civilization(
            "dense", geography=_SOLO_GEOGRAPHY,
            civilizations={"dense": _solo_civilization(10_000_000)})
        self.assertGreater(
            dense.price_kg_grain_equivalent_per_iugerum,
            sparse.price_kg_grain_equivalent_per_iugerum)
        # And both are strictly positive once ANY population presses on
        # the land - this is the exact defect Complaints/46 named: a
        # single, uniform region used to price at zero no matter how many
        # people depended on it.
        self.assertGreater(sparse.price_kg_grain_equivalent_per_iugerum, 0.0)

    def test_a_civilization_with_no_population_prices_at_zero(self):
        outcome = land.margin_outcome_for_civilization(
            "empty", geography=_SOLO_GEOGRAPHY,
            civilizations={"empty": _solo_civilization(0)})
        self.assertEqual(outcome.price_kg_grain_equivalent_per_iugerum, 0.0)

    def test_a_civilization_with_no_home_regions_prices_at_zero_not_crashing(self):
        outcome = land.margin_outcome_for_civilization(
            "landless", geography=_SOLO_GEOGRAPHY,
            civilizations={"landless": {"home_regions": [], "population": 1000}})
        self.assertEqual(outcome.price_kg_grain_equivalent_per_iugerum, 0.0)
        self.assertEqual(outcome.labour_hours_per_iugerum, 0.0)

    def test_rome_shows_both_margins_at_once(self):
        # The task's own "both must work together" requirement: a
        # civilization with varied land AND crowding should show BOTH
        # effects on its own better-than-marginal regions, not just one.
        # UPDATE (stakeholder maintainability item 6): allocations are now
        # keyed by TILE id, not region name, so "north_africa" is no
        # longer a key in `by_region` - it is 47 keys. Pick the BEST
        # north_africa tile (highest fertility - the one most likely to
        # sit above the marginal fertility and so show a nonzero extensive
        # rent) rather than an arbitrary one, so this assertion is not
        # flaky against whichever tile a dict happens to iterate first.
        geography = _real_geography()
        north_africa_tile_ids = set(
            geography["land_tiles"]["region_to_tiles"]["north_africa"])
        outcome = land.margin_outcome_for_civilization("rome_100ad")
        best_north_africa_tile = max(
            (a for a in outcome.allocations
             if a.region_land.region in north_africa_tile_ids),
            key=lambda a: a.fertility_quality_multiplier)
        self.assertGreater(
            best_north_africa_tile.extensive_rent_kg_grain_equivalent_per_iugerum,
            0.0)
        self.assertGreater(
            best_north_africa_tile.intensive_rent_kg_grain_equivalent_per_iugerum,
            0.0)
        self.assertAlmostEqual(
            best_north_africa_tile.rent_kg_grain_equivalent_per_iugerum,
            (best_north_africa_tile.extensive_rent_kg_grain_equivalent_per_iugerum
             + best_north_africa_tile.intensive_rent_kg_grain_equivalent_per_iugerum))

    def test_han_china_no_longer_prices_at_zero(self):
        # The task's own headline check, restated at the civilization
        # level rather than the ReferenceYield/MarginOfCultivation level -
        # see test_a_single_home_region_civilization_no_longer_prices_at_
        # zero above for the same claim with the extensive-component
        # breakdown asserted too.
        outcome = land.margin_outcome_for_civilization("han_china_100ad")
        self.assertGreater(outcome.price_kg_grain_equivalent_per_iugerum, 0.0)

    def test_abundant_land_per_head_is_cheaper_than_crowded_land(self):
        # The task's own explicit requirement: a civilization with
        # abundant land per head should still be cheaper than a crowded
        # one. Norse Scandinavia and Rome/Han China hold similarly
        # UNIFORM-ish territory (the Norse hold one region; so does Han
        # China), but the Norse have vastly more land per person than
        # either - this is a claim about POPULATION DENSITY on held
        # territory, not about fertility, so it should hold even though
        # the Norse's own land is also the least fertile of the three.
        norse = land.margin_outcome_for_civilization("norse_900ad")
        china = land.margin_outcome_for_civilization("han_china_100ad")
        rome = land.margin_outcome_for_civilization("rome_100ad")
        self.assertLess(
            norse.price_kg_grain_equivalent_per_iugerum,
            china.price_kg_grain_equivalent_per_iugerum)
        self.assertLess(
            norse.price_kg_grain_equivalent_per_iugerum,
            rome.price_kg_grain_equivalent_per_iugerum)

    def test_rome_still_outprices_the_norse_with_both_margins_active(self):
        # The pre-existing headline check (CivilizationTerritoryTests.
        # test_rome_outprices_the_norse) exercised the extensive margin
        # alone; this re-asserts the same ordering now that the intensive
        # margin is layered on top of it, so a future change to the
        # intensity mechanism cannot silently invert it.
        rome = land.margin_outcome_for_civilization("rome_100ad")
        norse = land.margin_outcome_for_civilization("norse_900ad")
        self.assertGreater(
            rome.price_kg_grain_equivalent_per_iugerum,
            norse.price_kg_grain_equivalent_per_iugerum)


if __name__ == "__main__":
    unittest.main()
