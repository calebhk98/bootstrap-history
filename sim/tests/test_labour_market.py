"""Regression tests for sim/world/labour_market.py.

Written as unittest.TestCase classes, like sim/tests/test_deposits.py,
sim/tests/test_land.py and sim/tests/test_demand.py: this module has no
dependency on sim/engine/ or any other sim/world/ module (see labour_
market.py's own STANDALONE section), so importing sim/tests/harness.py
would pull in the whole engine for no reason. sim/tests/__main__.py's own
_run_topic already runs both styles identically - this file's module name
for that registration is sim.tests.test_labour_market.

These checks are ORDERINGS AND STRUCTURAL PROPERTIES wherever a real
data/production/ figure is involved (a labour coefficient can be re-
authored at any confidence level without breaking this suite, exactly the
discipline sim/tests/test_deposits.py's own ExtractionCostMechanicsTests
docstring states for ore data), and EXACT ARITHMETIC wherever the input is
a small, hand-built synthetic fixture this file controls itself.
"""
import ast
import os
import subprocess
import sys
import unittest

from sim.world import labour_market

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


def _entry(outputs, labour_hours=None, capital=None):
    entry = {"outputs": outputs}
    if labour_hours is not None:
        entry["labour_hours"] = labour_hours
    if capital is not None:
        entry["capital"] = capital
    return entry


# ============================================================================
# DEMAND SIDE: HOURS REQUIRED PER TRADE FROM A PLANNED OUTPUT
# ============================================================================

class LabourHoursCoefficientsTests(unittest.TestCase):

    def test_single_output_single_trade_divides_by_the_batch_size(self):
        production = {"axe_kg": _entry({"axe_kg": 10.0}, {"smith": 5.0})}
        coefficients = labour_market.labour_hours_coefficients_per_unit_output(
            "axe_kg", production)
        self.assertAlmostEqual(coefficients["smith"], 0.5)

    def test_several_trades_each_get_their_own_coefficient(self):
        production = {"iron_bar_kg": _entry(
            {"iron_bar_kg": 1000.0}, {"furnaceman": 80.0, "smith": 120.0})}
        coefficients = labour_market.labour_hours_coefficients_per_unit_output(
            "iron_bar_kg", production)
        self.assertAlmostEqual(coefficients["furnaceman"], 0.08)
        self.assertAlmostEqual(coefficients["smith"], 0.12)

    def test_dominant_output_is_the_largest_by_mass_not_the_first_key(self):
        # zinc_electrolytic_kg-shaped entry: a tiny byproduct listed before
        # the real basis output. The coefficient must still be divided by
        # the BIG number, exactly as sim.world.demand's identical-shaped
        # helper does for `inputs`.
        production = {"smelt": _entry(
            {"byproduct_g": 0.5, "zinc_kg": 1000.0}, {"furnaceman": 200.0})}
        coefficients = labour_market.labour_hours_coefficients_per_unit_output(
            "smelt", production)
        self.assertAlmostEqual(coefficients["furnaceman"], 0.2)

    def test_capital_build_labour_hours_are_amortised_over_the_lifetime(self):
        production = {"pot_kg": _entry(
            {"pot_kg": 1000.0}, {"potter": 500.0},
            capital=[{"service_life_years": 10.0, "annual_output_at_basis": 1000.0,
                     "build_labour_hours": {"mason": 200.0}}])}
        coefficients = labour_market.labour_hours_coefficients_per_unit_output(
            "pot_kg", production)
        # 200 h to build, spread over 10 years * 1000 kg/year = 10,000 kg
        # of lifetime output -> 0.02 h/kg.
        self.assertAlmostEqual(coefficients["mason"], 0.02)
        self.assertAlmostEqual(coefficients["potter"], 0.5)

    def test_a_capital_item_missing_service_life_or_output_is_skipped_not_raised(self):
        production = {"widget_kg": _entry(
            {"widget_kg": 100.0}, {"labourer": 10.0},
            capital=[{"build_labour_hours": {"mason": 50.0}}])}
        coefficients = labour_market.labour_hours_coefficients_per_unit_output(
            "widget_kg", production)
        self.assertNotIn("mason", coefficients)

    def test_unknown_recipe_raises_key_error(self):
        with self.assertRaises(KeyError):
            labour_market.labour_hours_coefficients_per_unit_output(
                "not_a_real_recipe", {})

    def test_zero_basis_quantity_raises_value_error(self):
        production = {"broken": _entry({"broken_kg": 0.0}, {"labourer": 1.0})}
        with self.assertRaises(ValueError):
            labour_market.labour_hours_coefficients_per_unit_output(
                "broken", production)


class LabourHoursRequiredByTradeTests(unittest.TestCase):

    def setUp(self):
        self.production = {
            "wheat_kg": _entry({"wheat_kg": 577.5}, {"labourer": 150.0}),
            "iron_bar_kg": _entry({"iron_bar_kg": 1000.0},
                                  {"furnaceman": 80.0, "smith": 120.0}),
        }

    def test_aggregates_across_recipes_that_share_a_trade(self):
        production = {
            "a": _entry({"a_kg": 1.0}, {"labourer": 2.0}),
            "b": _entry({"b_kg": 1.0}, {"labourer": 3.0}),
        }
        hours_by_trade, _ = labour_market.labour_hours_required_by_trade(
            {"a": 10.0, "b": 10.0}, production)
        self.assertAlmostEqual(hours_by_trade["labourer"], 20.0 + 30.0)

    def test_breakdown_names_which_recipe_contributed_how_much(self):
        hours_by_trade, contributors = labour_market.labour_hours_required_by_trade(
            {"wheat_kg": 577.5, "iron_bar_kg": 1000.0}, self.production)
        self.assertAlmostEqual(hours_by_trade["labourer"], 150.0)
        self.assertAlmostEqual(hours_by_trade["smith"], 120.0)
        self.assertAlmostEqual(contributors["smith"]["iron_bar_kg"], 120.0)

    def test_a_recipe_not_in_production_is_silently_skipped(self):
        hours_by_trade, _ = labour_market.labour_hours_required_by_trade(
            {"no_such_recipe": 1000.0}, self.production)
        self.assertEqual(hours_by_trade, {})

    def test_a_zero_output_level_contributes_nothing(self):
        hours_by_trade, _ = labour_market.labour_hours_required_by_trade(
            {"wheat_kg": 0.0}, self.production)
        self.assertEqual(hours_by_trade, {})

    def test_output_level_scales_linearly(self):
        hours_at_1x, _ = labour_market.labour_hours_required_by_trade(
            {"wheat_kg": 577.5}, self.production)
        hours_at_3x, _ = labour_market.labour_hours_required_by_trade(
            {"wheat_kg": 3 * 577.5}, self.production)
        self.assertAlmostEqual(hours_at_3x["labourer"], 3 * hours_at_1x["labourer"])


class RealProductionDataSmokeTests(unittest.TestCase):
    """A light touch of the real data/production/*.json files - enough to
    prove the loader and the aggregation work against the genuine schema,
    never enough to assert a particular authored number (that is
    data/production/'s own owner's call, not this module's - see
    data/production/_SCHEMA.md and CLAUDE.md section 4)."""

    def test_wheat_kg_is_present_and_booked_to_labourer(self):
        production = labour_market.production_data()
        self.assertIn("wheat_kg", production)
        coefficients = labour_market.labour_hours_coefficients_per_unit_output(
            "wheat_kg", production)
        self.assertIn("labourer", coefficients)
        self.assertGreater(coefficients["labourer"], 0.0)

    def test_iron_bar_kg_needs_both_furnaceman_and_smith(self):
        production = labour_market.production_data()
        coefficients = labour_market.labour_hours_coefficients_per_unit_output(
            "iron_bar_kg", production)
        self.assertIn("furnaceman", coefficients)
        self.assertIn("smith", coefficients)

    def test_labour_hours_required_by_trade_runs_over_real_data(self):
        production = labour_market.production_data()
        hours_by_trade, _ = labour_market.labour_hours_required_by_trade(
            {"wheat_kg": 1_000_000.0, "iron_bar_kg": 10_000.0}, production)
        self.assertGreater(hours_by_trade.get("labourer", 0.0), 0.0)
        self.assertGreater(hours_by_trade.get("smith", 0.0), 0.0)


# ============================================================================
# THE BRIDGE TO A MARGINAL PRODUCT
# ============================================================================

class AdditionalHoursToCloseAShortfallTests(unittest.TestCase):

    def test_is_the_plain_inverse_of_the_marginal_product(self):
        self.assertAlmostEqual(
            labour_market.additional_hours_to_close_a_shortfall(100.0, 2.0), 50.0)

    def test_zero_marginal_product_raises_rather_than_dividing_by_zero(self):
        with self.assertRaises(ValueError):
            labour_market.additional_hours_to_close_a_shortfall(100.0, 0.0)

    def test_negative_marginal_product_also_raises(self):
        with self.assertRaises(ValueError):
            labour_market.additional_hours_to_close_a_shortfall(100.0, -1.0)


# ============================================================================
# THE ALLOCATION: Workforce.step
# ============================================================================

class WorkforceStepConservationTests(unittest.TestCase):

    def test_total_hours_are_unchanged_by_one_step(self):
        workforce = labour_market.Workforce(
            {"smith": 1000.0, "labourer": 5000.0, "potter": 2000.0})
        total_before = workforce.total_hours()
        workforce.step({"smith": 2000.0, "labourer": 4000.0, "potter": 2000.0})
        self.assertAlmostEqual(workforce.total_hours(), total_before)

    def test_conservation_holds_across_many_steps_with_a_changing_trade_set(self):
        workforce = labour_market.Workforce({"smith": 1000.0, "potter": 3000.0})
        total_before = workforce.total_hours()
        # `mason` appears only in demand, never in the starting workforce -
        # exercises the union-of-trade-names path in `step`.
        for _ in range(20):
            workforce.step({"smith": 1500.0, "mason": 200.0})
        self.assertAlmostEqual(workforce.total_hours(), total_before)


class WorkforceStepDirectionTests(unittest.TestCase):

    def test_hours_move_from_surplus_into_shortage(self):
        workforce = labour_market.Workforce({"smith": 1000.0, "potter": 3000.0})
        flows = workforce.step({"smith": 1500.0, "potter": 2500.0})
        self.assertGreater(flows["smith"].hours_after, flows["smith"].hours_before)
        self.assertLess(flows["potter"].hours_after, flows["potter"].hours_before)

    def test_a_trade_exactly_at_its_requirement_does_not_move(self):
        workforce = labour_market.Workforce({"smith": 1000.0, "potter": 1000.0})
        flows = workforce.step({"smith": 1000.0, "potter": 500.0})
        self.assertAlmostEqual(flows["smith"].hours_after, 1000.0)

    def test_a_trade_at_zero_hours_cannot_grow_however_large_the_shortage(self):
        workforce = labour_market.Workforce({"electrician": 0.0, "potter": 3000.0})
        flows = workforce.step({"electrician": 1_000_000.0, "potter": 0.0})
        self.assertEqual(flows["electrician"].hours_after, 0.0)
        self.assertEqual(flows["electrician"].hours_moved_in, 0.0)

    def test_minimum_absorption_seeds_a_trade_a_caller_says_now_exists(self):
        workforce = labour_market.Workforce({"electrician": 0.0, "potter": 3000.0})
        flows = workforce.step(
            {"electrician": 1_000_000.0, "potter": 0.0},
            minimum_absorption_hours_by_trade={"electrician": 100.0})
        self.assertAlmostEqual(flows["electrician"].hours_after, 100.0)

    def test_tightness_ratio_above_one_means_short_below_one_means_slack(self):
        workforce = labour_market.Workforce({"smith": 1000.0, "potter": 1000.0})
        flows = workforce.step({"smith": 2000.0, "potter": 500.0})
        self.assertGreater(flows["smith"].tightness_ratio, 1.0)
        self.assertLess(flows["potter"].tightness_ratio, 1.0)

    def test_tightness_ratio_is_infinite_for_a_nonexistent_trade_still_required(self):
        workforce = labour_market.Workforce({"potter": 3000.0})
        flows = workforce.step({"electrician": 500.0, "potter": 0.0})
        self.assertEqual(flows["electrician"].tightness_ratio, float("inf"))


class WorkforceStepMobilityBoundTests(unittest.TestCase):
    """`Workforce.step` no longer has ONE mobility rate - it has a steady-
    state rate, a gap-responsive gain on top of it, and a hard ceiling (see
    labour_market.py's THE FRICTION section). These tests check the
    CEILING (never exceeded, whatever the gap or the base rate), and that
    the rate genuinely moves with the two things it is now supposed to
    respond to: the SIZE of the gap (stakeholder points 3 and 4) and the
    base rate itself, in the regime where the ceiling is not yet binding.
    """

    def test_outflow_never_exceeds_the_ceiling_rate_times_the_trades_own_size(self):
        workforce = labour_market.Workforce({"potter": 10_000.0, "smith": 100.0})
        flows = workforce.step({"potter": 0.0, "smith": 1_000_000.0},
                               mobility_rate_per_year=0.05)
        ceiling = labour_market.OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR
        self.assertLessEqual(flows["potter"].hours_moved_out, 10_000.0 * ceiling + 1e-6)

    def test_inflow_never_exceeds_the_ceiling_rate_times_the_trades_own_size(self):
        # smith's own shortage (999,900h) dwarfs its own size (100h), so its
        # gap-responsive rate saturates at the ceiling - this is exactly the
        # regime OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR exists for.
        # `walkable_trades=frozenset()` isolates that arithmetic from
        # `smith`'s OWN, unrelated status in `WALKABLE_TRADES` (real
        # data/production/ now has smith reachable with no technology at
        # all - see TechnologyGatedWalkabilityTests - which would otherwise
        # let the seed-share reference, not this trade's OWN size, set the
        # ceiling this test means to check).
        workforce = labour_market.Workforce({"potter": 10_000.0, "smith": 100.0})
        flows = workforce.step({"potter": 0.0, "smith": 1_000_000.0},
                               mobility_rate_per_year=0.05, walkable_trades=frozenset())
        ceiling = labour_market.OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR
        self.assertLessEqual(flows["smith"].hours_moved_in, 100.0 * ceiling + 1e-6)
        self.assertAlmostEqual(flows["smith"].hours_moved_in, 100.0 * ceiling)

    def test_a_bigger_relative_gap_moves_more_in_one_step_same_base_rate(self):
        # The stakeholder's points 3 and 4, stated as a monotonicity check
        # rather than a specific number of years: doubling a trade's own
        # size (a 100% gap) pulls harder than nudging it 10%, holding the
        # trade's own size and the base rate fixed. `potter` is a large,
        # non-binding surplus source in both cases so `smith`'s own
        # gap-responsive ceiling is what is actually being measured.
        def moved_in(required_smith):
            workforce = labour_market.Workforce({"smith": 1000.0, "potter": 1_000_000.0})
            flows = workforce.step({"smith": required_smith, "potter": 0.0})
            return flows["smith"].hours_moved_in

        small_relative_gap = moved_in(1100.0)     # +10% of smith's own size
        large_relative_gap = moved_in(5000.0)     # +400% of smith's own size
        self.assertGreater(large_relative_gap, small_relative_gap)

    def test_a_higher_base_rate_moves_at_least_as_much_when_the_gap_is_small(self):
        def moved_in(base_rate):
            workforce = labour_market.Workforce({"smith": 1000.0, "potter": 1_000_000.0})
            # `walkable_trades=frozenset()` - see the identical note on
            # test_inflow_never_exceeds_the_ceiling_rate_times_the_trades_
            # own_size above: this test means to compare two RATES against
            # smith's own 1,000h size, and `potter`'s own 1,000,000h would
            # otherwise inflate the seed-share reference far past that,
            # capping both rates' inflow at the same gap-limited number and
            # erasing the very difference this test checks for.
            flows = workforce.step({"smith": 1050.0, "potter": 0.0},
                                   mobility_rate_per_year=base_rate,
                                   walkable_trades=frozenset())
            return flows["smith"].hours_moved_in

        self.assertGreater(moved_in(0.20), moved_in(0.02))

    def test_a_base_rate_above_the_default_ceiling_is_never_capped_below_itself(self):
        # A caller passing mobility_rate_per_year=1.0 (sim.tests.test_
        # labour_market.py's own WorkforceStepProportionalSplitExact
        # ArithmeticTests does exactly this, to make mobility itself a
        # non-binding constraint) must get AT LEAST that rate's worth of
        # ceiling, never the module's own smaller default ceiling instead -
        # see _gap_responsive_mobility_rate's own docstring for why the
        # effective ceiling is max(rate_ceiling, base_rate).
        self.assertLess(labour_market.OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR, 1.0)
        rate = labour_market._gap_responsive_mobility_rate(1.0, 5.0)
        self.assertAlmostEqual(rate, 1.0)


class GapResponsiveMobilityRateTests(unittest.TestCase):
    """Direct, hand-checkable coverage of the two pure functions THE
    FRICTION section's rate schedule is built from - see labour_market.py's
    own `_relative_gap_size` and `_gap_responsive_mobility_rate`."""

    def test_relative_gap_size_is_the_plain_ratio_when_basis_is_positive(self):
        self.assertAlmostEqual(labour_market._relative_gap_size(-50.0, 100.0), 0.5)
        self.assertAlmostEqual(labour_market._relative_gap_size(300.0, 100.0), 3.0)

    def test_relative_gap_size_is_zero_when_there_is_no_gap(self):
        self.assertEqual(labour_market._relative_gap_size(0.0, 0.0), 0.0)
        self.assertEqual(labour_market._relative_gap_size(0.0, 500.0), 0.0)

    def test_relative_gap_size_is_infinite_when_basis_is_zero_and_a_gap_exists(self):
        self.assertEqual(labour_market._relative_gap_size(50.0, 0.0), float("inf"))

    def test_zero_relative_gap_returns_exactly_the_base_rate(self):
        self.assertAlmostEqual(
            labour_market._gap_responsive_mobility_rate(0.05, 0.0), 0.05)

    def test_rate_rises_monotonically_with_relative_gap_up_to_the_ceiling(self):
        rate_at_small_gap = labour_market._gap_responsive_mobility_rate(0.05, 0.1)
        rate_at_large_gap = labour_market._gap_responsive_mobility_rate(0.05, 10.0)
        ceiling = labour_market.OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR
        self.assertGreater(rate_at_large_gap, rate_at_small_gap)
        self.assertLessEqual(rate_at_large_gap, ceiling)
        self.assertAlmostEqual(rate_at_large_gap, ceiling)

    def test_infinite_relative_gap_returns_exactly_the_ceiling(self):
        self.assertAlmostEqual(
            labour_market._gap_responsive_mobility_rate(0.05, float("inf")),
            labour_market.OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR)


class WalkableTradeSeedingTests(unittest.TestCase):
    """Stakeholder point 5: 'monster towers suddenly appeared, this also
    says 0 people will become adventurers'. A trade in `walkable_trades`
    can grow from exactly zero because it draws its mobility ceiling from
    `WALKABLE_TRADE_SEED_SHARE_OF_ECONOMY_HOURS` of the WHOLE economy
    instead of a share of its own (absent) size; a trade that is not
    walkable still cannot, which is this module's own documented,
    unchanged behaviour for a trade that needs a master (WHAT THIS DOES
    NOT MODEL item 2) - both are exercised side by side here so neither
    passing is an accident of the other's absence.
    """

    def _economy(self):
        # `labourer` carries a real surplus (120,000h have against 100,000h
        # need) so there is something in this fixture for either new trade
        # to draw on under this module's strict conservation of hours -
        # see Workforce.step's own docstring, step 5.
        return labour_market.Workforce(
            {"labourer": 120_000.0, "adventurer": 0.0, "optician": 0.0})

    def test_a_walkable_trade_at_zero_hours_moves(self):
        workforce = self._economy()
        flows = workforce.step(
            {"labourer": 100_000.0, "adventurer": 50_000.0, "optician": 0.0},
            walkable_trades=labour_market.WALKABLE_TRADES | {"adventurer"})
        self.assertGreater(flows["adventurer"].hours_moved_in, 0.0)
        self.assertGreater(workforce.hours_by_trade["adventurer"], 0.0)

    def test_a_non_walkable_trade_at_zero_hours_still_does_not_move(self):
        workforce = self._economy()
        flows = workforce.step(
            {"labourer": 100_000.0, "adventurer": 0.0, "optician": 50_000.0},
            walkable_trades=labour_market.WALKABLE_TRADES | {"adventurer"})
        self.assertEqual(flows["optician"].hours_moved_in, 0.0)
        self.assertEqual(workforce.hours_by_trade["optician"], 0.0)

    def test_default_walkable_trades_is_exactly_the_no_technology_computation(self):
        # WALKABLE_TRADES is no longer a hand-written list (see
        # TechnologyGatedWalkabilityTests below for the mechanism itself,
        # tested against a synthetic, hand-built production fixture) - it
        # is `trades_reachable_given_technology()` evaluated with no nodes
        # reached at all, computed once at import time. This checks that
        # self-consistency directly, against the REAL data/production/
        # files, without hardcoding what the data currently says (which
        # would be exactly the "hand-written list" defect this module
        # docstring's stakeholder point 8 asks to be rid of).
        self.assertEqual(labour_market.WALKABLE_TRADES,
                         labour_market.trades_reachable_given_technology())

    def test_labourer_and_miner_remain_walkable_under_the_new_computation(self):
        # A backward-compatibility smoke check, not a hardcoded outcome:
        # data/production/'s own labourer and miner entries include many
        # requires_node: null recipes (general digging and hauling), so
        # both trades were already, and remain, walkable with no
        # technology reached at all.
        self.assertIn("labourer", labour_market.WALKABLE_TRADES)
        self.assertIn("miner", labour_market.WALKABLE_TRADES)

    def test_walkable_trades_is_a_proper_subset_of_all_named_trades(self):
        # The computation must actually discriminate - if every trade
        # data/production/ names came out walkable with no technology
        # reached, the mechanism would not be doing the job the
        # stakeholder's "no nuclear engineer in Rome" half asked for.
        production = labour_market.production_data()
        all_trades = set()
        for entry in production.values():
            all_trades.update((entry.get("labour_hours") or {}).keys())
            for capital_item in entry.get("capital") or []:
                all_trades.update((capital_item.get("build_labour_hours") or {}).keys())
        self.assertTrue(labour_market.WALKABLE_TRADES)
        self.assertLess(labour_market.WALKABLE_TRADES, all_trades)

    def test_a_walkable_trades_own_growth_is_still_bounded_not_instant(self):
        # It moves, but it does not close a huge shortage in a single year -
        # this module is still a step process (see the module docstring's
        # WHY THIS IS A STEP PROCESS section), even for a walkable trade.
        workforce = self._economy()
        flows = workforce.step(
            {"labourer": 100_000.0, "adventurer": 50_000.0, "optician": 0.0},
            walkable_trades=labour_market.WALKABLE_TRADES | {"adventurer"})
        self.assertLess(flows["adventurer"].hours_after, 50_000.0)


class SeedReferenceBasisTests(unittest.TestCase):
    """QUESTION TWO the stakeholder asked: '1% of the whole economy's
    current hours, instead of a percentage of its own size, [means] year 2
    will have fewer people go to it? I'm suspicious of that.' Tested
    directly: `Workforce.step` takes `max(hours_before, seed_reference)`
    as the ceiling basis for a walkable trade (see `Workforce.step`'s own
    docstring, step 3), not a hard switch from one to the other - these
    tests are the exact-arithmetic proof that this is what stops the
    stall the stakeholder suspected, and a regression guard against ever
    changing `max` back into a switch keyed on `hours_before == 0`."""

    def test_seed_reference_basis_persists_while_the_trade_is_smaller_than_it(self):
        # A demand so large that the gap-responsive rate saturates at the
        # ceiling in every year shown (relative_gap stays huge), so the
        # amount moved in is exactly `ceiling_rate * ceiling_basis` with no
        # other effect to confound the comparison. seed_reference here is
        # 1% of 120,000 h = 1,200 h; `adventurer` stays below that for
        # (at least) its first two years, so both years must use the SAME
        # basis and therefore move the SAME amount - a stall would show up
        # as the second year moving markedly less than the first.
        workforce = labour_market.Workforce({"labourer": 120_000.0, "adventurer": 0.0})
        required = {"labourer": 70_000.0, "adventurer": 1_000_000.0}
        walkable = labour_market.WALKABLE_TRADES | {"adventurer"}
        first_year = workforce.step(required, walkable_trades=walkable)
        second_year = workforce.step(required, walkable_trades=walkable)
        self.assertGreater(first_year["adventurer"].hours_moved_in, 0.0)
        self.assertAlmostEqual(
            first_year["adventurer"].hours_moved_in,
            second_year["adventurer"].hours_moved_in)

    def test_the_basis_switches_to_the_trades_own_size_only_once_it_is_bigger(self):
        # Once the trade's own hours_before exceeds the seed reference,
        # its OWN size becomes the (larger) basis - `max`, not the seed
        # reference forever. This is the mirror check: the mechanism does
        # not overshoot into ignoring the trade's real size once it no
        # longer needs the seed's help.
        workforce = labour_market.Workforce({"labourer": 120_000.0, "adventurer": 2_000.0})
        required = {"labourer": 70_000.0, "adventurer": 1_000_000.0}
        walkable = labour_market.WALKABLE_TRADES | {"adventurer"}
        seed_reference = labour_market.WALKABLE_TRADE_SEED_SHARE_OF_ECONOMY_HOURS * 122_000.0
        self.assertGreater(2_000.0, seed_reference)   # the fixture's own precondition
        flows = workforce.step(required, walkable_trades=walkable)
        ceiling = labour_market.OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR
        self.assertAlmostEqual(flows["adventurer"].hours_moved_in, 2_000.0 * ceiling)

    def test_a_non_walkable_trade_never_gets_the_seed_reference_at_all(self):
        # The seed reference is only ever added on TOP of a trade's own
        # size for a WALKABLE trade - a non-walkable trade at zero still
        # has a ceiling basis of exactly zero, so it still cannot move
        # (WHAT THIS DOES NOT MODEL item 2's genuine limit, unchanged).
        workforce = labour_market.Workforce({"labourer": 120_000.0, "optician": 0.0})
        required = {"labourer": 70_000.0, "optician": 1_000_000.0}
        flows = workforce.step(required, walkable_trades=labour_market.WALKABLE_TRADES)
        self.assertEqual(flows["optician"].hours_moved_in, 0.0)


class TechnologyGatedWalkabilityTests(unittest.TestCase):
    """Stakeholder point 8 (module docstring): 'is the current labour
    market making it impossible for new trades to appear ... does this
    make blacksmiths impossible?' and 'you can't just make a nuclear
    engineer in Rome, so some limits are needed'. `trades_reachable_
    given_technology` is the general mechanism WALKABLE_TRADES is now
    built from - these are hand-built, synthetic production fixtures (this
    file's own EXACT ARITHMETIC discipline for a fixture it controls
    itself), so a re-authoring of the REAL data/production/ files cannot
    change what these tests prove."""

    def test_a_recipe_needing_no_technology_at_all_makes_its_trade_reachable(self):
        production = {"axe_kg": _entry({"axe_kg": 10.0}, {"smith": 5.0})}
        production["axe_kg"]["requires_node"] = None
        self.assertIn("smith", labour_market.trades_reachable_given_technology(
            reached_node_ids=(), production=production))

    def test_a_recipe_gated_behind_an_unreached_node_is_not_reachable(self):
        production = {"steel_kg": _entry({"steel_kg": 10.0}, {"smith": 5.0})}
        production["steel_kg"]["requires_node"] = "cementation_steel"
        self.assertNotIn("smith", labour_market.trades_reachable_given_technology(
            reached_node_ids=(), production=production))

    def test_reaching_the_gating_node_makes_the_trade_reachable(self):
        production = {"steel_kg": _entry({"steel_kg": 10.0}, {"smith": 5.0})}
        production["steel_kg"]["requires_node"] = "cementation_steel"
        self.assertIn("smith", labour_market.trades_reachable_given_technology(
            reached_node_ids={"cementation_steel"}, production=production))

    def test_an_unclassified_entry_missing_requires_node_grants_no_walkability(self):
        # No `requires_node` key at all - "nobody has classified this
        # entry", per data/production/_SCHEMA.md's own rule, which grants
        # no walkability at ANY reached_node_ids, not even the empty one.
        production = {"mystery_kg": _entry({"mystery_kg": 10.0}, {"smith": 5.0})}
        self.assertNotIn("smith", labour_market.trades_reachable_given_technology(
            reached_node_ids=(), production=production))
        self.assertNotIn("smith", labour_market.trades_reachable_given_technology(
            reached_node_ids={"anything"}, production=production))

    def test_a_capital_items_build_labour_hours_trade_is_covered_too(self):
        production = {"pot_kg": _entry(
            {"pot_kg": 10.0}, {"potter": 5.0},
            capital=[{"service_life_years": 10.0, "annual_output_at_basis": 10.0,
                     "build_labour_hours": {"mason": 20.0}}])}
        production["pot_kg"]["requires_node"] = None
        reachable = labour_market.trades_reachable_given_technology(
            reached_node_ids=(), production=production)
        self.assertIn("potter", reachable)
        self.assertIn("mason", reachable)

    def test_one_walkable_recipe_is_enough_even_if_others_for_the_same_trade_are_gated(self):
        # A smith with ONE hand-forging recipe needing no technology and
        # ANOTHER, more advanced recipe that does is still a smith a
        # civilisation can grow from zero - this module aggregates a
        # trade's hours across every recipe everywhere else, so it is
        # equally coarse here.
        production = {
            "iron_sheet_kg": _entry({"iron_sheet_kg": 10.0}, {"smith": 5.0}),
            "fine_steel_kg": _entry({"fine_steel_kg": 10.0}, {"smith": 5.0}),
        }
        production["iron_sheet_kg"]["requires_node"] = None
        production["fine_steel_kg"]["requires_node"] = "cementation_steel"
        self.assertIn("smith", labour_market.trades_reachable_given_technology(
            reached_node_ids=(), production=production))

    def test_more_reached_nodes_never_shrinks_the_walkable_set(self):
        production = {
            "a": _entry({"a_kg": 1.0}, {"labourer": 1.0}),
            "b": _entry({"b_kg": 1.0}, {"smith": 1.0}),
            "c": _entry({"c_kg": 1.0}, {"electrician": 1.0}),
        }
        production["a"]["requires_node"] = None
        production["b"]["requires_node"] = "blast_furnace"
        production["c"]["requires_node"] = "dynamo"
        with_none_reached = labour_market.trades_reachable_given_technology(
            reached_node_ids=(), production=production)
        with_one_reached = labour_market.trades_reachable_given_technology(
            reached_node_ids={"blast_furnace"}, production=production)
        with_both_reached = labour_market.trades_reachable_given_technology(
            reached_node_ids={"blast_furnace", "dynamo"}, production=production)
        self.assertLessEqual(with_none_reached, with_one_reached)
        self.assertLessEqual(with_one_reached, with_both_reached)
        self.assertEqual(with_none_reached, {"labourer"})
        self.assertEqual(with_one_reached, {"labourer", "smith"})
        self.assertEqual(with_both_reached, {"labourer", "smith", "electrician"})
        # "You can't just make a nuclear engineer in Rome" - the genuine
        # limit stays a limit until its own node is actually reached.
        self.assertNotIn("electrician", with_none_reached)
        self.assertNotIn("electrician", with_one_reached)


class EarlyCivilisationBlacksmithTests(unittest.TestCase):
    """QUESTION ONE the stakeholder asked, answered with a measurement
    against the REAL data/production/ files (a light touch, like
    RealProductionDataSmokeTests above, never asserting a number that data/
    production/'s own owner could re-author without breaking this suite):
    an early civilisation with EXACTLY ZERO smiths, that wants iron goods,
    is not stuck at zero forever."""

    def test_smith_is_walkable_with_no_technology_reached_at_all(self):
        # Grounded in a real, named entry: data/production/10_ferrous.json's
        # `iron_sheet_kg` needs no invented technology to hand-forge a
        # sheet from a bar (`requires_node: null`) - this is the measured
        # fact this whole mechanism is built from, not an assumption this
        # module makes about smiths.
        self.assertIn("smith", labour_market.WALKABLE_TRADES)

    def test_a_civilisation_with_zero_smiths_grows_one_from_nothing(self):
        production = labour_market.production_data()
        early_civilisation_workforce = {"labourer": 200_000.0, "smith": 0.0}
        iron_goods_hours_required, _ = labour_market.labour_hours_required_by_trade(
            {"iron_sheet_kg": 100_000.0}, production)
        self.assertGreater(iron_goods_hours_required.get("smith", 0.0), 0.0)
        outcome = labour_market.solve_to_stable_allocation(
            early_civilisation_workforce, iron_goods_hours_required,
            tolerance_hours=1.0, maximum_periods=200)
        self.assertGreater(outcome.workforce.hours_by_trade.get("smith", 0.0), 0.0)
        self.assertTrue(outcome.stabilized)
        self.assertLess(outcome.unmet_demand_by_trade.get("smith", 0.0),
                        iron_goods_hours_required["smith"])

    def test_a_trade_with_no_production_data_at_all_still_cannot(self):
        # The genuine limit named alongside the blacksmith question: a
        # trade this project has recorded NOTHING about (no data/
        # production/ entry at all - unlike smith, which has several) is
        # unclassified, not gate-satisfied, and stays unreachable at any
        # reached_node_ids. `optician` is this module's own worked-example
        # stand-in for exactly that case (see SCENARIO 3).
        self.assertNotIn("optician", labour_market.WALKABLE_TRADES)
        self.assertNotIn("optician", labour_market.trades_reachable_given_technology(
            reached_node_ids={"anything", "everything"}))


class SkillFamilyProximityTests(unittest.TestCase):
    """Stakeholder point 6: 'it thinks you can't ever teach yourself a
    skill, and nothing transfers'. A single surplus trade whose outflow
    cannot fill BOTH of two shortage trades' full requirement should
    favour the skill-close one - see TRADE_SKILL_FAMILY and
    `_flow_proximity`."""

    def test_same_family_destination_is_never_discounted(self):
        self.assertEqual(labour_market.trade_skill_family("furnaceman"), "metal")
        self.assertEqual(labour_market.trade_skill_family("smith"), "metal")
        self.assertEqual(
            labour_market._flow_proximity("furnaceman", "smith", destination_is_walkable=False),
            1.0)

    def test_cross_family_destination_is_discounted_by_the_stated_constant(self):
        self.assertEqual(labour_market.trade_skill_family("scribe"), "technical")
        self.assertEqual(
            labour_market._flow_proximity("furnaceman", "scribe", destination_is_walkable=False),
            labour_market.CROSS_FAMILY_PROXIMITY)

    def test_a_walkable_destination_is_never_discounted_regardless_of_family(self):
        self.assertEqual(
            labour_market._flow_proximity("scribe", "labourer", destination_is_walkable=True),
            1.0)

    def test_proximity_is_asymmetric_moving_down_into_unskilled_work_is_easier(self):
        # smith -> labourer (destination walkable): full proximity.
        # labourer -> smith (destination is a skilled, cross-family trade):
        # discounted - the same pair, opposite direction, different answer.
        down = labour_market._flow_proximity("smith", "labourer", destination_is_walkable=True)
        upward = labour_market._flow_proximity("labourer", "smith", destination_is_walkable=False)
        self.assertEqual(down, 1.0)
        self.assertLess(upward, down)

    def test_a_skill_close_shortage_trade_is_favoured_over_a_distant_one(self):
        # furnaceman (metal) is the only surplus trade; smith (metal, same
        # family) and scribe (technical, different family) both want more
        # than furnaceman's capped outflow can supply between them, so the
        # skill-close one should come out ahead.
        workforce = labour_market.Workforce(
            {"furnaceman": 10_000.0, "smith": 1_000.0, "scribe": 1_000.0})
        flows = workforce.step(
            {"furnaceman": 10_000.0 - 2_000.0, "smith": 1_000.0 + 2_000.0,
             "scribe": 1_000.0 + 2_000.0},
            mobility_rate_per_year=1.0)
        self.assertGreater(flows["smith"].hours_moved_in, flows["scribe"].hours_moved_in)
        # Conservation still holds across the two-destination split.
        self.assertAlmostEqual(
            flows["smith"].hours_moved_in + flows["scribe"].hours_moved_in,
            flows["furnaceman"].hours_moved_out)


class WorkforceStepProportionalSplitExactArithmeticTests(unittest.TestCase):
    """A hand-checkable case: two surplus trades of very different sizes,
    one shortage trade, mobility rate high enough that both surplus
    trades' caps are set by their SURPLUS rather than the mobility rate,
    so the split is exact arithmetic this test can verify by hand."""

    def test_shortage_trade_receives_the_smaller_of_supply_and_its_own_gap(self):
        # potter surplus: 500 h available to give up (mobility rate is not
        # the binding constraint here - the surplus itself is smaller).
        # smith surplus: 300 h available to give up, same reasoning.
        # labourer shortage: needs 400 h. Total supply (800h) exceeds the
        # 400h shortage, so labourer's inflow is capped at exactly 400h,
        # NOT at the full 800h available - `actual_total_moved` is the
        # smaller of the two totals by construction.
        workforce = labour_market.Workforce(
            {"potter": 10_000.0, "smith": 10_000.0, "labourer": 10_000.0})
        flows = workforce.step(
            {"potter": 10_000.0 - 500.0, "smith": 10_000.0 - 300.0,
             "labourer": 10_000.0 + 400.0},
            mobility_rate_per_year=1.0)
        self.assertAlmostEqual(flows["labourer"].hours_moved_in, 400.0)
        self.assertAlmostEqual(flows["labourer"].hours_after, 10_400.0)
        # The 400h actually moved is split across the two surplus trades
        # in proportion to their OWN capped outflow (500 and 300, out of
        # 800 total) - potter gives up 500/800 * 400 = 250h, smith gives
        # up 300/800 * 400 = 150h.
        self.assertAlmostEqual(flows["potter"].hours_moved_out, 250.0)
        self.assertAlmostEqual(flows["smith"].hours_moved_out, 150.0)


# ============================================================================
# THE FIXED POINT: solve_to_stable_allocation
# ============================================================================

class SolveToStableAllocationTests(unittest.TestCase):
    """`solve_to_stable_allocation` now ALWAYS returns a `LabourMarketOutcome`
    - see the module docstring's WHY DEMAND EXCEEDING SUPPLY DOES NOT MEAN A
    FAILED SOLVE. `stabilized` answers "has the allocation stopped moving",
    which is true both when every gap closes and when the trades with slack
    have already given up everything they can - `unmet_demand_by_trade` is
    what tells the two apart, and these tests check both regimes."""

    def test_converges_for_a_solvable_gap_within_available_slack(self):
        initial = {"potter": 10_000.0, "smith": 1_000.0}
        required = {"potter": 9_500.0, "smith": 1_500.0}
        outcome = labour_market.solve_to_stable_allocation(
            initial, required, tolerance_hours=1e-3)
        self.assertTrue(outcome.stabilized)
        self.assertGreater(outcome.periods_used, 1)   # friction means it is not instant
        self.assertAlmostEqual(outcome.workforce.hours_by_trade["smith"], 1_500.0, places=1)
        self.assertAlmostEqual(outcome.workforce.hours_by_trade["potter"], 9_500.0, places=1)
        self.assertEqual(outcome.unmet_demand_by_trade, {})

    def test_a_demand_vector_exceeding_total_supply_still_stabilizes_with_unmet_demand_named(self):
        # THE STAKEHOLDER'S OWN POINTS 1 AND 2: "even though my request
        # hours are more than the supply of labour hours, it should still
        # stabilize" and "supply can't match demand, but that's basically
        # 90% of society IRL. It still stabilizes." `potter` has nothing to
        # give (it is exactly at its own requirement), so `smith` cannot
        # grow AT ALL from this starting point - the honest "reallocation
        # of the EXISTING workforce cannot solve this" answer, now
        # returned as `stabilized=True` (the allocation truly has stopped
        # moving) with the shortfall named in `unmet_demand_by_trade`,
        # NEVER as a bare `False` that reads like a search failure.
        initial = {"potter": 100.0, "smith": 100.0}
        required = {"potter": 100.0, "smith": 100_000.0}
        outcome = labour_market.solve_to_stable_allocation(
            initial, required, maximum_periods=50)
        self.assertTrue(outcome.stabilized)
        self.assertLess(outcome.periods_used, 50)   # settles long before the ceiling
        self.assertAlmostEqual(outcome.workforce.hours_by_trade["smith"], 100.0)
        self.assertAlmostEqual(outcome.unmet_demand_by_trade["smith"], 99_900.0)
        self.assertNotIn("potter", outcome.unmet_demand_by_trade)

    def test_a_demand_vector_already_met_converges_on_the_first_period(self):
        initial = {"potter": 5_000.0, "smith": 500.0}
        required = dict(initial)
        outcome = labour_market.solve_to_stable_allocation(initial, required)
        self.assertTrue(outcome.stabilized)
        self.assertEqual(outcome.periods_used, 1)
        self.assertEqual(outcome.unmet_demand_by_trade, {})

    def test_history_length_matches_periods_used(self):
        initial = {"potter": 10_000.0, "smith": 1_000.0}
        required = {"potter": 9_000.0, "smith": 2_000.0}
        outcome = labour_market.solve_to_stable_allocation(
            initial, required, tolerance_hours=1e-3)
        self.assertEqual(len(outcome.history), outcome.periods_used)

    def test_a_previously_unreachable_shortage_now_settles_far_faster(self):
        # The exact fixture the old flat-rate mechanism took 500 periods
        # (the old MAXIMUM_REALLOCATION_PERIODS) to fail to converge on -
        # a war-sized shock a small trade cannot fully absorb from a tiny
        # surplus pool - now stabilizes in a handful of years, because the
        # surplus side's own gap-responsive rate drains its slack quickly
        # rather than trickling it out at a flat 5%/year forever.
        initial = {"potter": 12_000.0, "smith": 1_000.0}
        required = {"potter": 10_000.0, "smith": 3_000.0}
        outcome = labour_market.solve_to_stable_allocation(
            initial, required, tolerance_hours=1.0, maximum_periods=500)
        self.assertTrue(outcome.stabilized)
        self.assertLess(outcome.periods_used, 30)

    def test_walkable_trades_and_other_step_kwargs_pass_through(self):
        initial = {"labourer": 120_000.0, "adventurer": 0.0}
        required = {"labourer": 100_000.0, "adventurer": 20_000.0}
        outcome = labour_market.solve_to_stable_allocation(
            initial, required, tolerance_hours=1.0, maximum_periods=200,
            walkable_trades=labour_market.WALKABLE_TRADES | {"adventurer"})
        self.assertGreater(outcome.workforce.hours_by_trade["adventurer"], 0.0)


# ============================================================================
# WHAT WAS NOT MET, AND HAVE VERSUS NEED
# ============================================================================

class UnmetDemandByTradeTests(unittest.TestCase):

    def test_only_positive_shortfalls_are_reported(self):
        result = labour_market.unmet_demand_by_trade(
            {"smith": 100.0, "potter": 500.0}, {"smith": 150.0, "potter": 400.0})
        self.assertEqual(result, {"smith": 50.0})
        self.assertNotIn("potter", result)

    def test_a_fully_met_allocation_reports_an_empty_dict(self):
        self.assertEqual(
            labour_market.unmet_demand_by_trade({"smith": 100.0}, {"smith": 100.0}), {})

    def test_a_trade_required_but_entirely_absent_is_its_own_full_shortfall(self):
        result = labour_market.unmet_demand_by_trade({}, {"electrician": 40.0})
        self.assertEqual(result, {"electrician": 40.0})


class HaveVersusNeedTests(unittest.TestCase):
    """The module docstring's central reframe, made callable - see `have_
    versus_need`'s own docstring for the stakeholder quotation it answers."""

    def test_reports_both_numbers_and_their_gap_for_every_named_trade(self):
        result = labour_market.have_versus_need(
            {"smith": 800.0}, {"smith": 1_000.0, "potter": 200.0})
        self.assertEqual(result["smith"].hours_have, 800.0)
        self.assertEqual(result["smith"].hours_need, 1_000.0)
        self.assertEqual(result["smith"].gap, 200.0)
        self.assertEqual(result["potter"].hours_have, 0.0)
        self.assertEqual(result["potter"].hours_need, 200.0)

    def test_a_negative_gap_means_have_exceeds_need(self):
        result = labour_market.have_versus_need({"smith": 1_200.0}, {"smith": 1_000.0})
        self.assertEqual(result["smith"].gap, -200.0)
        self.assertLess(result["smith"].tightness_ratio, 1.0)

    def test_tightness_ratio_is_infinite_when_have_is_zero_and_need_is_not(self):
        result = labour_market.have_versus_need({}, {"electrician": 40.0})
        self.assertEqual(result["electrician"].tightness_ratio, float("inf"))


# ============================================================================
# THE FRICTION CONSTANTS
# ============================================================================

class OccupationalMobilityRateTests(unittest.TestCase):

    def test_is_a_plausible_fraction_strictly_between_zero_and_one(self):
        self.assertGreater(labour_market.OCCUPATIONAL_MOBILITY_RATE_PER_YEAR, 0.0)
        self.assertLess(labour_market.OCCUPATIONAL_MOBILITY_RATE_PER_YEAR, 1.0)

    def test_is_declared_as_a_labelled_temporary_heuristic(self):
        from sim import constants
        entry = constants.REGISTRY["OCCUPATIONAL_MOBILITY_RATE_PER_YEAR"]
        self.assertEqual(entry["kind"], "temporary_heuristic")
        self.assertTrue(entry["why"])
        self.assertTrue(entry["source"])


class MobilityFrictionConstantsTests(unittest.TestCase):
    """The three constants THE FRICTION section added alongside the
    original steady-state rate, each labelled per CLAUDE.md SS3.4."""

    def test_gap_response_gain_is_positive_and_labelled(self):
        from sim import constants
        self.assertGreater(labour_market.OCCUPATIONAL_MOBILITY_GAP_RESPONSE_GAIN, 0.0)
        entry = constants.REGISTRY["OCCUPATIONAL_MOBILITY_GAP_RESPONSE_GAIN"]
        self.assertEqual(entry["kind"], "temporary_heuristic")
        self.assertTrue(entry["why"])

    def test_rate_ceiling_is_above_the_steady_state_rate_and_below_one(self):
        from sim import constants
        self.assertGreater(labour_market.OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR,
                           labour_market.OCCUPATIONAL_MOBILITY_RATE_PER_YEAR)
        self.assertLess(labour_market.OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR, 1.0)
        entry = constants.REGISTRY["OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR"]
        self.assertEqual(entry["kind"], "temporary_heuristic")
        self.assertTrue(entry["why"])

    def test_walkable_seed_share_is_a_small_positive_fraction(self):
        from sim import constants
        self.assertGreater(labour_market.WALKABLE_TRADE_SEED_SHARE_OF_ECONOMY_HOURS, 0.0)
        self.assertLess(labour_market.WALKABLE_TRADE_SEED_SHARE_OF_ECONOMY_HOURS, 1.0)
        entry = constants.REGISTRY["WALKABLE_TRADE_SEED_SHARE_OF_ECONOMY_HOURS"]
        self.assertEqual(entry["kind"], "temporary_heuristic")
        self.assertTrue(entry["why"])

    def test_cross_family_proximity_is_a_fraction_strictly_between_zero_and_one(self):
        from sim import constants
        self.assertGreater(labour_market.CROSS_FAMILY_PROXIMITY, 0.0)
        self.assertLess(labour_market.CROSS_FAMILY_PROXIMITY, 1.0)
        entry = constants.REGISTRY["CROSS_FAMILY_PROXIMITY"]
        self.assertEqual(entry["kind"], "temporary_heuristic")
        self.assertTrue(entry["why"])


# ============================================================================
# STANDALONE ON PURPOSE
# ============================================================================

class StandaloneImportTests(unittest.TestCase):
    """sim/world/labour_market.py must not import sim/engine/, sim/
    solve_prices.py, or any other sim/world/ module AS PART OF ITS
    IMPORTABLE SURFACE - see its own docstring's STANDALONE section and
    sim/world/__init__.py for why every module in this package holds to
    this independently. The ONE deliberate exception (see the module
    docstring) is its own `__main__` demonstration block, which imports
    sim.world.agriculture to get a real marginal-product number for the
    worked example - this test checks the TOP-LEVEL module body only, so
    that exception does not silently widen into the importable surface
    other modules actually depend on.
    """

    def _top_level_imports(self):
        path = os.path.join(_REPO_ROOT, "sim", "world", "labour_market.py")
        with open(path) as handle:
            tree = ast.parse(handle.read(), filename=path)
        imported = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        return imported

    def test_top_level_imports_are_limited_to_stdlib_and_sim_constants(self):
        imported = self._top_level_imports()
        for name in imported:
            self.assertFalse(
                name.startswith("sim.engine"),
                "sim/world/labour_market.py imports %r at module level" % name)
            self.assertFalse(
                name.startswith("sim.world.") and name != "sim.world.labour_market",
                "sim/world/labour_market.py imports another sim/world/ "
                "module at module level: %r" % name)
            self.assertNotEqual(
                name, "sim.solve_prices",
                "sim/world/labour_market.py imports the price solver "
                "directly at module level")

    def test_the_only_other_sim_world_import_is_inside_the_main_guard(self):
        path = os.path.join(_REPO_ROOT, "sim", "world", "labour_market.py")
        with open(path) as handle:
            tree = ast.parse(handle.read(), filename=path)
        top_level_kinds = {type(node) for node in tree.body}
        # There must be at least one `if __name__ == "__main__":` block
        # for the demo's own import to live inside, or this test would be
        # vacuously trusting an import that is not actually confined.
        self.assertIn(ast.If, top_level_kinds)

        agriculture_imports_outside_main_guard = []
        for node in tree.body:
            if isinstance(node, ast.If):
                continue   # the demo block - permitted to import agriculture
            for inner in ast.walk(node):
                if isinstance(inner, ast.ImportFrom) and inner.module == "sim.world":
                    for alias in inner.names:
                        if alias.name == "agriculture":
                            agriculture_imports_outside_main_guard.append(node)
        self.assertEqual(agriculture_imports_outside_main_guard, [])


# ============================================================================
# python3 -m sim.world.labour_market MUST RUN CLEANLY
# ============================================================================

class ModuleRunsCleanlyTests(unittest.TestCase):

    def test_main_block_runs_and_tells_both_scenarios(self):
        result = subprocess.run(
            [sys.executable, "-m", "sim.world.labour_market"],
            cwd=_REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SCENARIO 1", result.stdout)
        self.assertIn("SCENARIO 2", result.stdout)
        self.assertIn("SCENARIO 5", result.stdout)
        self.assertIn("smith", result.stdout)
        self.assertIn("labourer", result.stdout)


if __name__ == "__main__":
    unittest.main()
