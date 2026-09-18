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
import os
import unittest

from sim.world import land

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


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
        rome_lands = land.cultivable_land_for_civilization("rome_100ad")
        rome_regions = {rl.region for rl in rome_lands}
        self.assertEqual(
            rome_regions,
            {"italia", "gaul_germania", "britannia", "hispania",
             "north_africa", "greece_anatolia", "levant_mesopotamia"})

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
        self.assertEqual(len(expanded_lands), 2)
        self.assertEqual(len(shrunk_lands), 1)
        total_arable = sum(rl.arable_iugera for rl in expanded_lands)
        shrunk_arable = sum(rl.arable_iugera for rl in shrunk_lands)
        self.assertGreater(total_arable, shrunk_arable)

    def test_unknown_civilization_raises_with_the_real_list(self):
        with self.assertRaises(FileNotFoundError):
            land.cultivable_land_for_civilization("atlantis_9999ad")

    def test_a_region_missing_a_land_block_is_skipped_not_fatal(self):
        civilization = {"home_regions": ["italia", "nowhere_at_all"]}
        lands = land.cultivable_land_for_civilization(
            "hypothetical", civilizations={"hypothetical": civilization})
        self.assertEqual([rl.region for rl in lands], ["italia"])

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

    def test_a_single_home_region_civilization_prices_land_at_zero(self):
        # Han China and the Norse both hold exactly one home region this
        # round - see the module docstring for why that is a genuine
        # finding (no differential rent without a worse region of their
        # OWN to compare against) rather than a bug this test should guard
        # against reappearing.
        for civilization_id in ("han_china_100ad", "norse_900ad"):
            outcome = land.margin_outcome_for_civilization(civilization_id)
            self.assertEqual(outcome.price_kg_grain_equivalent_per_iugerum, 0.0)


if __name__ == "__main__":
    unittest.main()
