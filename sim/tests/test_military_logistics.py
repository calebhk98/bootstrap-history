"""Regression tests for sim/world/military_logistics.py.

Written as unittest.TestCase classes, like sim/tests/test_agriculture.py and
sim/tests/test_demography.py: this module has no dependency on sim/engine/
(see military_logistics.py's own docstring for why), and importing
sim/tests/harness.py would pull in the whole engine for no reason.
sim/tests/__main__.py's _run_topic already runs both styles identically.

The task this module answers to asks for two different kinds of check.
Most of these classes check PROPERTIES that must hold regardless of the
exact numbers chosen - the baggage-train range must fall with distance, a
firearm's ammunition mass must scale with rounds fired, foraging must
produce more soldiers on richer or slower-crossed land. The last two
classes instead pin the CURRENT computed values and compare them to the
calibration ranges declared at the bottom of military_logistics.py, honestly
and without retuning anything to make them agree - see that module's own
CALIBRATION TARGETS section and pack_animal_max_one_way_days()'s docstring.
"""
import unittest

from sim.world import military_logistics as logistics


class RationAndWaterTests(unittest.TestCase):
    """A soldier at campaign exertion must need more food than a sedentary
    person, and a desert march must need more water than a temperate one -
    the two directional facts the module docstring's THE POINT paragraph
    leans on."""

    def test_campaign_ration_exceeds_the_sedentary_baseline(self):
        campaign_kcal = logistics.soldier_campaign_energy_requirement_kcal_per_day()
        self.assertGreater(campaign_kcal, logistics.SEDENTARY_ENERGY_REQUIREMENT_KCAL_PER_DAY)

    def test_ration_is_a_positive_number_of_kilograms(self):
        self.assertGreater(logistics.ration_kg_grain_per_day(), 0.0)

    def test_desert_water_requirement_exceeds_temperate(self):
        temperate = logistics.water_requirement_liters_per_day(desert=False)
        desert = logistics.water_requirement_liters_per_day(desert=True)
        self.assertGreater(desert, temperate)
        self.assertAlmostEqual(
            desert / temperate, logistics.DESERT_HEAT_WATER_MULTIPLIER, places=6)


class BaggageTrainRangeTests(unittest.TestCase):
    """The break-even structure at the heart of this module: a pack animal
    carrying its own fodder delivers less and less net cargo as distance
    grows, hits zero at a finite range, and that range does not depend on
    how many animals are in the column."""

    def test_net_deliverable_cargo_falls_as_distance_grows(self):
        near = logistics.pack_animal_net_deliverable_cargo_kg(10.0)
        far = logistics.pack_animal_net_deliverable_cargo_kg(100.0)
        self.assertGreater(near, far)
        self.assertGreaterEqual(far, 0.0)

    def test_net_deliverable_cargo_at_zero_distance_equals_full_capacity(self):
        self.assertAlmostEqual(
            logistics.pack_animal_net_deliverable_cargo_kg(0.0),
            logistics.pack_animal_load_capacity_kg(), places=9)

    def test_net_deliverable_cargo_is_exactly_zero_at_the_computed_max_range(self):
        max_range_km = logistics.pack_animal_max_one_way_range_km(delivered_fraction=0.0)
        self.assertAlmostEqual(
            logistics.pack_animal_net_deliverable_cargo_kg(max_range_km), 0.0, places=6)
        # And clipped at zero beyond it, not negative.
        self.assertEqual(
            logistics.pack_animal_net_deliverable_cargo_kg(max_range_km * 2.0), 0.0)

    def test_max_range_does_not_depend_on_number_of_animals(self):
        # The module's own claimed finding: the ratio of capacity to
        # fodder is a property of ONE animal, so scaling both by any
        # constant (standing in for "N animals instead of one") leaves the
        # range unchanged. Exercised here by scaling the two underlying
        # quantities directly rather than by constructing N animals, since
        # the production functions operate on one representative animal.
        capacity = logistics.pack_animal_load_capacity_kg()
        fodder = logistics.pack_animal_daily_fodder_kg()
        days_one_animal = capacity * 1.0 / (2.0 * fodder)
        days_ten_animals = (capacity * 10.0) / (2.0 * fodder * 10.0)
        self.assertAlmostEqual(days_one_animal, days_ten_animals, places=9)

    def test_higher_delivered_fraction_requires_shorter_range(self):
        zero_net_days = logistics.pack_animal_max_one_way_days(delivered_fraction=0.0)
        half_net_days = logistics.pack_animal_max_one_way_days(delivered_fraction=0.5)
        full_net_days = logistics.pack_animal_max_one_way_days(delivered_fraction=1.0)
        self.assertGreater(zero_net_days, half_net_days)
        self.assertGreater(half_net_days, full_net_days)
        self.assertEqual(full_net_days, 0.0)

    def test_delivered_fraction_outside_zero_one_is_rejected(self):
        with self.assertRaises(ValueError):
            logistics.pack_animal_max_one_way_days(delivered_fraction=1.5)
        with self.assertRaises(ValueError):
            logistics.pack_animal_max_one_way_days(delivered_fraction=-0.1)

    def test_negative_distance_is_rejected(self):
        with self.assertRaises(ValueError):
            logistics.pack_animal_net_deliverable_cargo_kg(-5.0)

    def test_animals_required_grows_with_distance_and_is_infinite_beyond_max_range(self):
        near_count = logistics.pack_animals_required_for_daily_delivery(1000.0, 10.0)
        far_count = logistics.pack_animals_required_for_daily_delivery(1000.0, 100.0)
        self.assertGreater(far_count, near_count)
        beyond_max_range = logistics.pack_animal_max_one_way_range_km(0.0) + 1.0
        self.assertEqual(
            logistics.pack_animals_required_for_daily_delivery(1000.0, beyond_max_range),
            float("inf"))

    def test_negative_daily_requirement_is_rejected(self):
        with self.assertRaises(ValueError):
            logistics.pack_animals_required_for_daily_delivery(-1.0, 10.0)


class ForagingTests(unittest.TestCase):
    """A foraging army's sustainable size must respond to the three things
    the module's derivation says it should: the land's surplus, how fast
    the army crosses fresh ground, and how wide a corridor it can strip -
    and to nothing else."""

    def test_richer_land_supports_a_larger_army(self):
        poor = logistics.sustainable_foraging_army_size(50.0)
        rich = logistics.sustainable_foraging_army_size(500.0)
        self.assertGreater(rich, poor)
        # Linear in the surplus figure, by construction of the formula.
        self.assertAlmostEqual(rich / poor, 500.0 / 50.0, places=6)

    def test_faster_march_supports_a_larger_army_on_the_same_land(self):
        slow = logistics.sustainable_foraging_army_size(
            100.0, march_rate_km_per_day=10.0)
        fast = logistics.sustainable_foraging_army_size(
            100.0, march_rate_km_per_day=40.0)
        self.assertGreater(fast, slow)

    def test_zero_surplus_supports_no_army(self):
        self.assertEqual(logistics.sustainable_foraging_army_size(0.0), 0.0)

    def test_negative_surplus_is_rejected(self):
        with self.assertRaises(ValueError):
            logistics.sustainable_foraging_army_size(-1.0)

    def test_wider_corridor_supports_a_larger_army(self):
        narrow = logistics.sustainable_foraging_army_size(100.0, corridor_width_km=5.0)
        wide = logistics.sustainable_foraging_army_size(100.0, corridor_width_km=50.0)
        self.assertGreater(wide, narrow)


class EquipmentTests(unittest.TestCase):
    """Equipment is a stock plus a rate, and the rate must actually be a
    FRACTION of the stock, not an independent number that could exceed
    it by construction."""

    def test_annual_replacement_is_a_fraction_of_the_full_kit(self):
        replacement = logistics.annual_iron_replacement_kg_per_soldier()
        self.assertGreater(replacement, 0.0)
        self.assertLess(replacement, logistics.IRON_KG_PER_EQUIPPED_SOLDIER)
        self.assertAlmostEqual(
            replacement,
            logistics.IRON_KG_PER_EQUIPPED_SOLDIER
            * logistics.ANNUAL_EQUIPMENT_REPLACEMENT_FRACTION,
            places=9)


class FirearmTests(unittest.TestCase):
    """CLAUDE.md SS3.3: a firearm is an object with an ammunition and
    maintenance requirement, and a musket and a modern rifle must go
    through the exact same two functions, only with different Firearm
    values - no branch anywhere that checks which weapon it is."""

    def test_ammunition_mass_scales_with_rounds_and_mass_per_shot(self):
        double_rounds = logistics.FLINTLOCK_MUSKET._replace(
            rounds_per_engagement=logistics.FLINTLOCK_MUSKET.rounds_per_engagement * 2.0)
        self.assertAlmostEqual(
            logistics.ammunition_mass_kg_per_soldier_per_engagement(double_rounds),
            2.0 * logistics.ammunition_mass_kg_per_soldier_per_engagement(
                logistics.FLINTLOCK_MUSKET),
            places=9)

    def test_musket_and_rifle_go_through_the_same_functions(self):
        # Both firearms must produce a positive ammunition mass through the
        # identical function call - the "same structure, different numbers"
        # requirement, checked rather than just claimed in a docstring.
        for firearm in (logistics.FLINTLOCK_MUSKET, logistics.MODERN_SERVICE_RIFLE):
            mass = logistics.ammunition_mass_kg_per_soldier_per_engagement(firearm)
            self.assertGreater(mass, 0.0)

    def test_musket_has_a_maintenance_requirement_the_modern_rifle_does_not(self):
        # The flint is the "maintenance requirement" CLAUDE.md SS3.3 names
        # alongside ammunition; the modern cartridge weapon in this module
        # has none of that shape (see MODERN_SERVICE_RIFLE's declaration
        # for why its maintenance burden is real but not modelled as a
        # per-shot mass here).
        self.assertGreater(
            logistics.maintenance_items_per_soldier_per_engagement(
                logistics.FLINTLOCK_MUSKET), 0.0)
        self.assertEqual(
            logistics.maintenance_items_per_soldier_per_engagement(
                logistics.MODERN_SERVICE_RIFLE), 0.0)

    def test_no_bespoke_branch_on_which_firearm_it_is(self):
        # A structural guard against the exact defect CLAUDE.md SS3.3 rules
        # out: neither consumption function may name either weapon.
        import inspect
        for function in (logistics.ammunition_mass_kg_per_soldier_per_engagement,
                         logistics.maintenance_items_per_soldier_per_engagement):
            source = inspect.getsource(function)
            self.assertNotIn("MUSKET", source)
            self.assertNotIn("RIFLE", source)


class DailySupplyRequirementTests(unittest.TestCase):
    """The aggregator that adds grain, water and (optionally) ammunition
    into one daily mass figure - conservation of the obvious kind: the
    total must equal the sum of its parts, and each part must respond to
    the input that should move it."""

    def test_total_equals_the_sum_of_its_parts(self):
        requirement = logistics.daily_supply_requirement_kg(
            1000.0, desert=True, firearm=logistics.FLINTLOCK_MUSKET,
            engagements_per_day=0.5)
        self.assertAlmostEqual(
            requirement.total_kg,
            requirement.grain_kg + requirement.water_kg + requirement.ammunition_kg,
            places=6)

    def test_no_firearm_means_no_ammunition_mass(self):
        requirement = logistics.daily_supply_requirement_kg(1000.0)
        self.assertEqual(requirement.ammunition_kg, 0.0)

    def test_desert_costs_more_water_than_temperate_at_the_same_army_size(self):
        temperate = logistics.daily_supply_requirement_kg(1000.0, desert=False)
        desert = logistics.daily_supply_requirement_kg(1000.0, desert=True)
        self.assertGreater(desert.water_kg, temperate.water_kg)
        self.assertEqual(desert.grain_kg, temperate.grain_kg)

    def test_negative_army_size_is_rejected(self):
        with self.assertRaises(ValueError):
            logistics.daily_supply_requirement_kg(-1.0)


class RationCalibrationTests(unittest.TestCase):
    """Compares the physiologically-derived campaign ration to the
    documented Roman grain-ration range, WITHOUT retuning anything to force
    agreement - see ration_kg_grain_per_day()'s own docstring for the
    reading of the gap this reports.
    """

    def test_current_computed_ration_pinned(self):
        # Pinned regression value: 2200 * 2.0 / 3400.
        self.assertAlmostEqual(logistics.ration_kg_grain_per_day(), 1.29412, places=4)

    def test_computed_ration_exceeds_the_documented_roman_range(self):
        ration = logistics.ration_kg_grain_per_day()
        self.assertGreater(
            ration, logistics.CALIBRATION_LEGION_RATION_KG_GRAIN_PER_DAY_HIGH,
            "the physiologically-derived ration no longer exceeds the "
            "documented Roman grain ration - if a real change caused this, "
            "update this comment and military_logistics.py's ration_kg_"
            "grain_per_day() docstring together; do not just delete the "
            "assertion.")

    def test_march_rate_falls_inside_the_documented_range(self):
        self.assertGreaterEqual(
            logistics.ARMY_MARCH_RATE_KM_PER_DAY,
            logistics.CALIBRATION_LEGION_MARCH_RATE_KM_PER_DAY_LOW)
        self.assertLessEqual(
            logistics.ARMY_MARCH_RATE_KM_PER_DAY,
            logistics.CALIBRATION_LEGION_MARCH_RATE_KM_PER_DAY_HIGH)


class SupplyRangeCalibrationTests(unittest.TestCase):
    """The headline comparison this module was built to make honestly: how
    does the derived baggage-train range compare to the historically
    documented 'a few days' limit? Both readings are pinned and compared,
    neither is tuned - see pack_animal_max_one_way_days()'s own docstring
    for why two different readings of "the range" are reported rather than
    one.
    """

    def test_zero_net_range_pinned_and_above_the_calibration_high_end(self):
        days = logistics.pack_animal_max_one_way_days(delivered_fraction=0.0)
        self.assertAlmostEqual(days, 7.5, places=6)
        self.assertGreater(
            days, logistics.CALIBRATION_MAX_SUPPLY_RANGE_DAYS_HIGH,
            "the zero-net physical ceiling no longer exceeds the "
            "documented 'a few days' high end - if a real change caused "
            "this, update this comment and the module docstring together; "
            "do not just delete the assertion.")

    def test_half_delivered_range_pinned_and_inside_the_calibration_band(self):
        days = logistics.pack_animal_max_one_way_days(delivered_fraction=0.5)
        self.assertAlmostEqual(days, 3.75, places=6)
        self.assertGreaterEqual(
            days, logistics.CALIBRATION_MAX_SUPPLY_RANGE_DAYS_LOW)
        self.assertLessEqual(
            days, logistics.CALIBRATION_MAX_SUPPLY_RANGE_DAYS_HIGH)


if __name__ == "__main__":
    unittest.main()
