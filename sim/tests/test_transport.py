"""Regression tests for sim/world/transport.py.

Written as unittest.TestCase classes, like sim/tests/test_agriculture.py and
sim/tests/test_demography.py, rather than the flat check()-at-import style
most topics use: this module has no dependency on sim/engine/ (see
transport.py's own docstring for why), and importing sim/tests/harness.py
would pull in the whole engine for no reason. sim/tests/__main__.py's
_run_topic already runs both styles identically - see its own docstring.

The task this module answers to is explicit that PLAUSIBILITY is not the
point, PROPERTIES are: a worse road surface must cost more cargo, a steeper
grade must cost more feed (and, for a wheeled vehicle, eventually all of its
capacity), water must be dramatically cheaper than a road for the same team,
downstream must differ from upstream, and a team's own feed must be able to
eat its entire cargo allowance past some distance. That is what each class
below checks. The one exception is HeadlineCalibrationTests, which compares
this module's own numbers to the Diocletian's-Edict-derived calibration
targets WITHOUT retuning anything to close a gap if one shows up - see that
class and transport.py's own CALIBRATION TARGETS docstring section for the
reading of where the two do and do not agree.
"""
import unittest

from sim.world import transport


class RollingResistanceOrdersSurfacesTests(unittest.TestCase):
    """The entire reason a road is worth building: the same team, the same
    vehicle, hauls less cargo as the surface's rolling-resistance
    coefficient rises. This is checked as an ORDERING, not against any
    particular number, because the coefficients themselves are engineering
    estimates - the ordering is the property that must hold regardless.
    """

    def test_paved_beats_dirt_beats_mud(self):
        paved = transport.max_cargo_mass_kg(
            transport.OX, 2, transport.CART, transport.PAVED_ROAD)
        dirt = transport.max_cargo_mass_kg(
            transport.OX, 2, transport.CART, transport.DIRT_TRACK)
        mud = transport.max_cargo_mass_kg(
            transport.OX, 2, transport.CART, transport.MUD)
        self.assertGreater(paved, dirt)
        self.assertGreater(dirt, mud)
        self.assertGreater(mud, 0.0)

    def test_feed_and_driver_hours_per_tonne_km_rise_with_resistance(self):
        # Less cargo for the same team and distance means the SAME feed and
        # driver time is spread over fewer tonne-km, so the per-tonne-km
        # figures must rise as the surface worsens - the mechanism by which
        # a bad road makes freight dearer without any price anywhere in
        # this module.
        paved = transport.draught_freight_physical_inputs(
            transport.OX, 2, transport.CART, transport.PAVED_ROAD)
        dirt = transport.draught_freight_physical_inputs(
            transport.OX, 2, transport.CART, transport.DIRT_TRACK)
        mud = transport.draught_freight_physical_inputs(
            transport.OX, 2, transport.CART, transport.MUD)
        self.assertLess(paved.feed_kg_per_tonne_km, dirt.feed_kg_per_tonne_km)
        self.assertLess(dirt.feed_kg_per_tonne_km, mud.feed_kg_per_tonne_km)
        self.assertLess(paved.driver_hours_per_tonne_km, dirt.driver_hours_per_tonne_km)
        self.assertLess(dirt.driver_hours_per_tonne_km, mud.driver_hours_per_tonne_km)


class TeamSizeAndBodyMassTests(unittest.TestCase):
    """Sanity checks on the parts of the physics that should be simple
    linear facts: a bigger team pulls harder, a heavier animal eats more
    just to exist.
    """

    def test_pull_force_is_linear_in_team_size(self):
        one = transport.sustained_pull_newtons(transport.OX, 1)
        four = transport.sustained_pull_newtons(transport.OX, 4)
        self.assertAlmostEqual(four, 4.0 * one, places=6)

    def test_cargo_capacity_increases_with_team_size(self):
        small = transport.max_cargo_mass_kg(
            transport.OX, 1, transport.CART, transport.DIRT_TRACK)
        large = transport.max_cargo_mass_kg(
            transport.OX, 4, transport.CART, transport.DIRT_TRACK)
        self.assertGreater(large, small)

    def test_maintenance_feed_rises_with_body_mass_sublinearly(self):
        # Kleiber's law: a heavier animal eats more, but less than
        # proportionally more - the sub-linear exponent is the whole point
        # of using it rather than a flat per-kg figure.
        lighter = transport.maintenance_kcal_per_day(transport.MULE)
        heavier = transport.maintenance_kcal_per_day(transport.HORSE)
        self.assertLess(lighter, heavier)
        mass_ratio = transport.HORSE.body_mass_kg / transport.MULE.body_mass_kg
        feed_ratio = heavier / lighter
        self.assertLess(feed_ratio, mass_ratio)

    def test_team_size_must_be_positive(self):
        with self.assertRaises(ValueError):
            transport.sustained_pull_newtons(transport.OX, 0)
        with self.assertRaises(ValueError):
            transport.max_pack_load_kg(transport.MULE, -1)


class GradientTests(unittest.TestCase):
    """Gradient is where wheeled and pack transport diverge sharply: a cart
    has to fight gravity through the SAME tractive-force ceiling that
    rolling resistance uses, and can be defeated by grade alone, while a
    pack animal's carrying capacity (a fraction of its own body weight) is
    untouched by grade - only its feed bill rises. This divergence is the
    mechanism this module gives for 'mountains are different', not a
    separate flag for mountainous terrain.
    """

    def test_steep_grade_collapses_cart_capacity_but_not_pack_capacity(self):
        flat_cart = transport.max_cargo_mass_kg(
            transport.OX, 2, transport.CART, transport.DIRT_TRACK, grade_fraction=0.0)
        steep_cart = transport.max_cargo_mass_kg(
            transport.OX, 2, transport.CART, transport.DIRT_TRACK,
            grade_fraction=transport.TYPICAL_MOUNTAIN_PASS_GRADE_FRACTION)
        self.assertGreater(flat_cart, steep_cart)
        # At this project's declared constants the grade very nearly wipes
        # out the cart's capacity outright - checked as a loose upper bound
        # rather than a pinned value, since it is one declared coefficient
        # away from actually reaching zero (see max_cargo_mass_kg's own
        # clamp for what happens then).
        self.assertLess(steep_cart, 0.01 * flat_cart)

        flat_pack = transport.max_pack_load_kg(transport.MULE, 1)
        steep_pack = transport.max_pack_load_kg(transport.MULE, 1)
        self.assertAlmostEqual(flat_pack, steep_pack, places=9,
            msg="max_pack_load_kg takes no grade argument at all - a pack "
                "animal's carrying capacity is a fact about its own body, "
                "not about the route, which is exactly the property this "
                "test is pinning down.")

    def test_pack_feed_rises_with_grade_even_though_capacity_does_not(self):
        flat = transport.pack_freight_physical_inputs(transport.MULE, 1, grade_fraction=0.0)
        steep = transport.pack_freight_physical_inputs(
            transport.MULE, 1, grade_fraction=transport.TYPICAL_MOUNTAIN_PASS_GRADE_FRACTION)
        self.assertAlmostEqual(flat.cargo_tonnes, steep.cargo_tonnes, places=9)
        self.assertGreater(steep.feed_kg_per_tonne_km, flat.feed_kg_per_tonne_km)

    def test_downhill_grade_costs_no_negative_work(self):
        # A descending pack route is not modelled as refunding calories -
        # see pack_climb_work_joules_per_day's own docstring for why that
        # is a real physical claim (muscle is not a generator), not a
        # missing feature.
        work = transport.pack_climb_work_joules_per_day(
            transport.MULE, 1, cargo_kg=50.0, grade_fraction=-0.08, distance_km=32.0)
        self.assertEqual(work, 0.0)

    def test_a_grade_steeper_than_available_pull_raises_a_clear_error(self):
        with self.assertRaises(ValueError):
            transport.max_cargo_mass_kg(
                transport.OX, 2, transport.CART, transport.PAVED_ROAD, grade_fraction=-1.0)


class WaterVersusLandTests(unittest.TestCase):
    """Buoyancy is the whole story: the same class of animal, at the same
    walking pace, delivers far more tonne-km per day, and at a far lower
    feed and driver-hour cost per tonne-km, once it no longer has to
    support the load's weight against the ground. Checked as orderings and
    a loose order-of-magnitude bound, never against a precise historical
    number - see HeadlineCalibrationTests for the one place this module
    compares itself to Diocletian's Edict, and does so honestly rather than
    by tuning anything here.
    """

    def test_water_delivers_far_more_tonne_km_per_day_than_a_road_cart(self):
        cart = transport.draught_freight_physical_inputs(
            transport.OX, 2, transport.CART, transport.DIRT_TRACK)
        barge = transport.barge_freight_physical_inputs(transport.HORSE, 1)
        self.assertGreater(barge.tonne_km_per_day, 10.0 * cart.tonne_km_per_day)

    def test_water_feed_and_driver_hours_per_tonne_km_are_far_lower(self):
        cart = transport.draught_freight_physical_inputs(
            transport.OX, 2, transport.CART, transport.DIRT_TRACK)
        barge = transport.barge_freight_physical_inputs(transport.HORSE, 1)
        self.assertGreater(cart.feed_kg_per_tonne_km, 5.0 * barge.feed_kg_per_tonne_km)
        self.assertGreater(cart.driver_hours_per_tonne_km, 5.0 * barge.driver_hours_per_tonne_km)

    def test_downstream_beats_calm_water_beats_upstream(self):
        calm = transport.barge_freight_physical_inputs(transport.HORSE, 1, current_km_per_hour=0.0)
        downstream = transport.barge_freight_physical_inputs(
            transport.HORSE, 1, current_km_per_hour=3.0)
        upstream = transport.barge_freight_physical_inputs(
            transport.HORSE, 1, current_km_per_hour=-3.0)
        self.assertGreater(downstream.tonne_km_per_day, calm.tonne_km_per_day)
        self.assertGreater(calm.tonne_km_per_day, upstream.tonne_km_per_day)
        # Same feed either way: the current changes ground speed, not the
        # hull's speed through the water, which is what the animal's own
        # work depends on - see barge_freight_physical_inputs's own
        # docstring for the mechanism.
        self.assertAlmostEqual(downstream.feed_kg_per_day, upstream.feed_kg_per_day, places=6)
        self.assertAlmostEqual(downstream.feed_kg_per_day, calm.feed_kg_per_day, places=6)

    def test_upstream_against_a_current_faster_than_the_tow_speed_is_impossible(self):
        too_fast = transport.HORSE.walking_speed_km_per_hour + 1.0
        with self.assertRaises(ValueError):
            transport.barge_freight_physical_inputs(
                transport.HORSE, 1, current_km_per_hour=-too_fast)


class SelfDefeatingRangeTests(unittest.TestCase):
    """The animal's own feed as cargo: past some one-way distance, hauling
    enough feed for the whole trip consumes the team's entire spare pulling
    capacity, so cargo delivered falls to zero even though the team never
    stops. See maximum_one_way_range_before_self_defeating_km's own
    docstring for the algebra and its named limitations (one-way only,
    force held at the full-load figure throughout the trip).
    """

    def test_range_is_positive_and_finite_at_reference_settings(self):
        km = transport.maximum_one_way_range_before_self_defeating_km(
            transport.OX, 2, transport.CART, transport.DIRT_TRACK)
        self.assertGreater(km, 0.0)
        self.assertLess(km, 1.0e7)

    def test_worse_surface_gives_a_shorter_self_defeating_range(self):
        # More feed burned per tonne-km hauled means the break-even point
        # arrives sooner - a worse road does not just cost more per
        # tonne-km, it shortens how far ANYTHING can economically go at
        # all.
        paved = transport.maximum_one_way_range_before_self_defeating_km(
            transport.OX, 2, transport.CART, transport.PAVED_ROAD)
        dirt = transport.maximum_one_way_range_before_self_defeating_km(
            transport.OX, 2, transport.CART, transport.DIRT_TRACK)
        mud = transport.maximum_one_way_range_before_self_defeating_km(
            transport.OX, 2, transport.CART, transport.MUD)
        self.assertGreater(paved, dirt)
        self.assertGreater(dirt, mud)

    def test_steeper_grade_gives_a_shorter_self_defeating_range(self):
        flat = transport.maximum_one_way_range_before_self_defeating_km(
            transport.OX, 2, transport.CART, transport.DIRT_TRACK, grade_fraction=0.0)
        graded = transport.maximum_one_way_range_before_self_defeating_km(
            transport.OX, 2, transport.CART, transport.DIRT_TRACK, grade_fraction=0.03)
        self.assertGreater(flat, graded)

    def test_a_team_that_cannot_move_its_own_vehicle_has_zero_range(self):
        km = transport.maximum_one_way_range_before_self_defeating_km(
            transport.OX, 2, transport.CART, transport.DIRT_TRACK,
            grade_fraction=transport.TYPICAL_MOUNTAIN_PASS_GRADE_FRACTION * 3.0)
        self.assertEqual(km, 0.0)


class DeterminismTests(unittest.TestCase):
    """This module draws no randomness at all - every function is a pure
    computation on its declared constants and its arguments - so, unlike
    sim/world/agriculture.py and sim/world/demography.py, there is no seed
    to hold fixed. What is worth pinning down instead is that calling the
    same function twice, with the same arguments, gives bit-identical
    results, which would only fail if some hidden mutable state crept in.
    """

    def test_repeated_calls_are_bit_identical(self):
        first = transport.draught_freight_physical_inputs(
            transport.OX, 2, transport.CART, transport.DIRT_TRACK,
            grade_fraction=0.02)
        second = transport.draught_freight_physical_inputs(
            transport.OX, 2, transport.CART, transport.DIRT_TRACK,
            grade_fraction=0.02)
        self.assertEqual(first, second)


class InputValidationTests(unittest.TestCase):
    """The physical quantities this module returns are meaningless, or
    outright undefined, outside certain ranges - a load fraction has to be
    a fraction, and a team that cannot move its own dead weight has no
    tonne-km to divide feed by. These should fail loudly, not return NaN
    or a negative cost.
    """

    def test_load_fraction_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            transport.draught_freight_physical_inputs(
                transport.OX, 2, transport.CART, transport.DIRT_TRACK, load_fraction=0.0)
        with self.assertRaises(ValueError):
            transport.draught_freight_physical_inputs(
                transport.OX, 2, transport.CART, transport.DIRT_TRACK, load_fraction=1.5)

    def test_a_team_defeated_by_its_own_vehicle_raises_rather_than_going_negative(self):
        with self.assertRaises(ValueError):
            transport.draught_freight_physical_inputs(
                transport.OX, 1, transport.WAGON, transport.MUD,
                grade_fraction=transport.TYPICAL_MOUNTAIN_PASS_GRADE_FRACTION)


class HeadlineCalibrationTests(unittest.TestCase):
    """The two calibration targets from transport.py's own module docstring
    and CALIBRATION TARGETS section, both traceable to Diocletian's Price
    Edict: land freight roughly 10-100x sea freight per unit distance, and
    grain uneconomical to haul much past 75-300 km overland. This suite
    does NOT retune anything to force either - see transport.py's own
    WATER_TRANSPORT_RESISTANCE_COEFFICIENT_AT_TOW_SPEED and CALIBRATION
    TARGETS declarations for the reading of why the results land where they
    do.

    THE HONEST READING, recorded here rather than only in a commit message:
    the LAND-TO-WATER RATIO lands close to the calibration range on both
    physical measures this module can produce (feed ~23x, driver-hours
    ~9.4x - the feed ratio sits inside 10-100x, the driver-hours ratio just
    under it), which is a real point in this derivation's favour given that
    neither ratio was tuned to land there. The SELF-DEFEATING RANGE is a
    different story: on ordinary surfaces (paved, dirt) it comes out three
    to twelve times LARGER than the 75-300 km historical range, because it
    answers a different question than the historical claim does. This
    module's range is the point where an ox team's OWN feed physically
    exhausts its pulling capacity - a hard physical wall. The historical
    75-300 km figure is an ECONOMIC threshold, the point where accumulated
    transport cost (feed, wages, wear, profit, risk, tolls) exceeds what a
    low-value bulky good like grain is worth per unit weight - which this
    module cannot compute at all without a grain price and a wage, both
    still missing from this project (see the module docstring's NOT A MONEY
    FIGURE section). The two thresholds are not the same thing and there is
    no reason to expect them to coincide; MUD's range (135 km) falls inside
    the historical window, but that is read here as roughly where physical
    exhaustion and economic ruin happen to overlap on the worst surface,
    not as the model being validated - see the module's own docstring for
    the same reading, and do not delete this paragraph to make the numbers
    look better than they are.
    """

    def test_land_to_water_ratio_is_a_well_defined_positive_number(self):
        cart = transport.draught_freight_physical_inputs(
            transport.OX, 2, transport.CART, transport.DIRT_TRACK)
        barge = transport.barge_freight_physical_inputs(transport.HORSE, 1)
        feed_ratio = cart.feed_kg_per_tonne_km / barge.feed_kg_per_tonne_km
        driver_ratio = cart.driver_hours_per_tonne_km / barge.driver_hours_per_tonne_km
        self.assertGreater(feed_ratio, 1.0)
        self.assertGreater(driver_ratio, 1.0)

    def test_feed_ratio_pinned_and_compared_to_the_edict_range(self):
        cart = transport.draught_freight_physical_inputs(
            transport.OX, 2, transport.CART, transport.DIRT_TRACK)
        barge = transport.barge_freight_physical_inputs(transport.HORSE, 1)
        feed_ratio = cart.feed_kg_per_tonne_km / barge.feed_kg_per_tonne_km
        self.assertAlmostEqual(feed_ratio, 22.74, places=1)
        self.assertGreaterEqual(feed_ratio, transport.LAND_TO_SEA_FREIGHT_COST_RATIO_LOW)
        self.assertLessEqual(feed_ratio, transport.LAND_TO_SEA_FREIGHT_COST_RATIO_HIGH)

    def test_driver_hours_ratio_pinned_and_compared_to_the_edict_range(self):
        cart = transport.draught_freight_physical_inputs(
            transport.OX, 2, transport.CART, transport.DIRT_TRACK)
        barge = transport.barge_freight_physical_inputs(transport.HORSE, 1)
        driver_ratio = cart.driver_hours_per_tonne_km / barge.driver_hours_per_tonne_km
        self.assertAlmostEqual(driver_ratio, 9.43, places=1)
        # Pinned as CURRENT behaviour, not corrected: this ratio actually
        # falls just under the calibration range's low end, and the
        # docstring above says so rather than silently rounding it in.
        self.assertLess(driver_ratio, transport.LAND_TO_SEA_FREIGHT_COST_RATIO_LOW)

    def test_self_defeating_range_pinned_and_compared_to_the_historical_window(self):
        paved = transport.maximum_one_way_range_before_self_defeating_km(
            transport.OX, 2, transport.CART, transport.PAVED_ROAD)
        dirt = transport.maximum_one_way_range_before_self_defeating_km(
            transport.OX, 2, transport.CART, transport.DIRT_TRACK)
        mud = transport.maximum_one_way_range_before_self_defeating_km(
            transport.OX, 2, transport.CART, transport.MUD)
        self.assertAlmostEqual(paved, 3070.4, places=0)
        self.assertAlmostEqual(dirt, 868.5, places=0)
        self.assertAlmostEqual(mud, 134.6, places=0)
        # Pinned as CURRENT behaviour: paved and dirt land ABOVE the
        # historical window (a different, harder physical limit than the
        # historical ECONOMIC one - see this class's own docstring), while
        # mud happens to land inside it.
        self.assertGreater(paved, transport.HISTORICAL_MAX_ECONOMIC_LAND_HAUL_KM_HIGH)
        self.assertGreater(dirt, transport.HISTORICAL_MAX_ECONOMIC_LAND_HAUL_KM_HIGH)
        self.assertGreaterEqual(mud, transport.HISTORICAL_MAX_ECONOMIC_LAND_HAUL_KM_LOW)
        self.assertLessEqual(mud, transport.HISTORICAL_MAX_ECONOMIC_LAND_HAUL_KM_HIGH)
