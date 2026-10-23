"""Round two of Complaints/43 on synthetic entries: a thermal requirement is graded per consumer, so a hot consumer never raises
a cooler consumer's price and a friction source never undercuts a fuel on cost alone. The solver functions are called on
entries built in the test; the two data tests read the reach each real heat source states. No game."""

QUICK_TOPIC = True

import unittest

from sim.engine import solve_prices


class CapabilityFloorByCarrierTests(unittest.TestCase):
    """`capability_floor_by_carrier` now returns ONLY the carrier's own
    universal default - see the module's own ROUND TWO paragraph above for
    why it must no longer be raised by what any consumer states. This is
    the opposite of what this same test class asserted before round two;
    that is the point of the fix, not an oversight in the old tests.
    """

    def test_the_default_floor_applies_with_no_active_consumer(self):
        floor = solve_prices.capability_floor_by_carrier({})
        self.assertEqual(floor["thermal_mj"],
                        solve_prices.THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C)

    def test_a_consumers_stated_need_no_longer_raises_the_shared_floor(self):
        # This is the exact scenario the old test suite's
        # "an_active_consumer_can_raise_the_floor_above_the_default" test
        # pinned as CORRECT - it was pinning the bug. A consumer's own
        # requirement is now graded separately (see
        # PerConsumerGradingTests below); it must not touch the shared
        # floor every OTHER, unlabelled consumer reads.
        entries = {
            "hot_process": {"outputs": {"widget_kg": 1.0}, "inputs": {},
                            "labour_hours": {}, "thermal_mj": 5.0,
                            "temperature_needed_c": 2000.0},
        }
        floor = solve_prices.capability_floor_by_carrier(entries)
        self.assertEqual(floor["thermal_mj"],
                        solve_prices.THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C)

    def test_a_stated_need_below_the_default_does_not_lower_it_either(self):
        entries = {
            "mild_process": {"outputs": {"widget_kg": 1.0}, "inputs": {},
                             "labour_hours": {}, "thermal_mj": 5.0,
                             "temperature_needed_c": 150.0},
        }
        floor = solve_prices.capability_floor_by_carrier(entries)
        self.assertEqual(floor["thermal_mj"],
                        solve_prices.THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C)


class CapabilityRequiredGradesTests(unittest.TestCase):
    """`capability_required_grades` - the set of distinct requirements this
    era's own entries actually state, which PER-CONSUMER GRADING solves
    once each, independently, rather than folding into one shared number.
    """

    def test_the_default_floor_is_always_present_even_with_no_consumers(self):
        grades = solve_prices.capability_required_grades({})
        self.assertEqual(grades["thermal_mj"],
                        (solve_prices.THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C,))

    def test_every_distinct_active_requirement_is_its_own_grade(self):
        entries = {
            "mild_process": {"outputs": {"a_kg": 1.0}, "inputs": {},
                             "labour_hours": {}, "thermal_mj": 5.0,
                             "temperature_needed_c": 1000.0},
            "hot_process": {"outputs": {"b_kg": 1.0}, "inputs": {},
                            "labour_hours": {}, "thermal_mj": 5.0,
                            "temperature_needed_c": 2500.0},
        }
        grades = solve_prices.capability_required_grades(entries)
        self.assertEqual(
            grades["thermal_mj"],
            (solve_prices.THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C, 1000.0, 2500.0))

    def test_a_consumer_that_does_not_draw_the_carrier_is_ignored(self):
        entries = {
            "irrelevant": {"outputs": {"widget_kg": 1.0}, "inputs": {},
                          "labour_hours": {}, "temperature_needed_c": 5000.0},
        }
        grades = solve_prices.capability_required_grades(entries)
        self.assertEqual(grades["thermal_mj"],
                        (solve_prices.THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C,))

    def test_a_consumer_with_no_stated_need_adds_no_grade(self):
        entries = {
            "unannotated": {"outputs": {"widget_kg": 1.0}, "inputs": {},
                           "labour_hours": {}, "thermal_mj": 5.0},
        }
        grades = solve_prices.capability_required_grades(entries)
        self.assertEqual(grades["thermal_mj"],
                        (solve_prices.THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C,))


class PerConsumerGradingTests(unittest.TestCase):
    """`capability_price_for_requirement` and the two acceptance scenarios
    this task names explicitly: a hot consumer existing anywhere must not
    move a cooler consumer's own price, and a low-temperature process and a
    high-temperature one must each get their own best technique, at the
    same time, in the same solved economy.
    """

    def _entries(self):
        # A cheap, low-reach source (friction, standing in for a warm
        # bearing off a water wheel) and a pricier, high-reach one
        # (charcoal), exactly the shape of the real England 1300 defect -
        # so the CHEAPER technique is also the one that cannot serve a
        # hot job, which is what makes this a meaningful test rather than
        # a trivial one where the cheapest option always wins anyway.
        return {
            "cheap_shaft": {"outputs": {"mechanical_mj": 1000.0}, "inputs": {},
                            "labour_hours": {"labourer": 0.001},
                            "requires_node": None},
            "friction": {"outputs": {"thermal_mj": 1000.0}, "inputs": {},
                        "labour_hours": {}, "mechanical_mj": 1.0,
                        "temperature_reached_c": 100.0, "requires_node": None},
            "real_fuel": {"outputs": {"thermal_mj": 1000.0}, "inputs": {},
                         "labour_hours": {"labourer": 10.0},
                         "temperature_reached_c": 1100.0, "requires_node": None},
        }

    def _solve(self, entries):
        wage_by_trade = {"labourer": 1.0}
        producers_of = solve_prices.build_producers_index(entries)
        resolvable = solve_prices.compute_resolvable_materials(entries, producers_of)
        return solve_prices.solve(entries, producers_of, resolvable, wage_by_trade)

    def test_a_low_temperature_process_can_use_a_low_temperature_source_while_a_high_temperature_one_exists(self):
        # Both requirements are graded AT ONCE, in the same solved
        # economy: the cool job gets friction (cheaper, and hot enough
        # for it), the hot job gets the real fuel (friction cannot reach
        # it), and neither answer depends on solving the other first.
        entries = self._entries()
        entries["dry_plaster"] = {
            "outputs": {"dry_plaster_widget_kg": 1.0}, "inputs": {},
            "labour_hours": {"labourer": 0.001}, "thermal_mj": 1.0,
            "temperature_needed_c": 100.0, "requires_node": None,
        }
        entries["melt_iron"] = {
            "outputs": {"melt_iron_widget_kg": 1.0}, "inputs": {},
            "labour_hours": {"labourer": 0.001}, "thermal_mj": 1.0,
            "temperature_needed_c": 1000.0, "requires_node": None,
        }
        prices, _iters, _residual, _chosen = self._solve(entries)

        low_price = solve_prices.capability_price_for_requirement(
            "thermal_mj", 100.0, entries, prices, {"labourer": 1.0})
        high_price = solve_prices.capability_price_for_requirement(
            "thermal_mj", 1000.0, entries, prices, {"labourer": 1.0})

        self.assertEqual(low_price[1], "friction")
        self.assertEqual(high_price[1], "real_fuel")
        self.assertLess(low_price[0], high_price[0])

        # And the SOLVED PRICES of the two consuming materials themselves
        # (not just the helper function in isolation) reflect exactly
        # this: the cool job's own material is cheaper than the hot job's,
        # because each was actually costed against its own graded price
        # inside `solve`, via `recipe_cost_and_allocation`.
        self.assertLess(prices["dry_plaster_widget_kg"], prices["melt_iron_widget_kg"])

    def test_a_hot_consumer_anywhere_does_not_raise_a_cooler_consumers_price(self):
        # THE STAKEHOLDER'S OWN EXAMPLE: inventing a 2500 C technique
        # (fission-hot, nothing to do with the cool job) must not touch
        # what the cool job pays.
        without_hot_consumer = self._entries()
        without_hot_consumer["dry_plaster"] = {
            "outputs": {"dry_plaster_widget_kg": 1.0}, "inputs": {},
            "labour_hours": {"labourer": 0.001}, "thermal_mj": 1.0,
            "temperature_needed_c": 150.0, "requires_node": None,
        }
        prices_before, _iterations, _residual, _chosen = self._solve(without_hot_consumer)

        with_hot_consumer = dict(without_hot_consumer)
        with_hot_consumer["fusion_forge"] = {
            "outputs": {"fusion_widget_kg": 1.0}, "inputs": {},
            "labour_hours": {"labourer": 0.001}, "thermal_mj": 1.0,
            "temperature_needed_c": 2500.0, "requires_node": None,
        }
        prices_after, _iterations, _residual, _chosen = self._solve(with_hot_consumer)

        self.assertEqual(prices_before["dry_plaster_widget_kg"],
                        prices_after["dry_plaster_widget_kg"])
        # And the generic, unlabelled thermal_mj pool price - what every
        # OTHER consumer with no stated requirement of its own pays - is
        # unaffected too.
        self.assertEqual(prices_before["thermal_mj"], prices_after["thermal_mj"])

    def test_a_cheap_cold_source_appearing_does_not_disturb_a_hot_consumer(self):
        # THE MIRROR CASE the stakeholder also named: a water wheel (a
        # cheap, merely-warm-via-friction source) appearing must not stop
        # a hot job from getting the hot technique it already needed.
        entries = self._entries()
        entries["melt_iron"] = {
            "outputs": {"melt_iron_widget_kg": 1.0}, "inputs": {},
            "labour_hours": {"labourer": 0.001}, "thermal_mj": 1.0,
            "temperature_needed_c": 1000.0, "requires_node": None,
        }
        prices, _iters, _residual, _chosen = self._solve(entries)
        hot_price = solve_prices.capability_price_for_requirement(
            "thermal_mj", 1000.0, entries, prices, {"labourer": 1.0})
        self.assertEqual(hot_price[1], "real_fuel")

    def test_a_requirement_nothing_can_meet_fails_honestly_rather_than_borrowing_a_cooler_grade(self):
        # No technique in this synthetic economy reaches 5000 C - the
        # honest answer is "no path to a price for this specific
        # requirement", never a silent fall-back to real_fuel's 1100 C
        # reach pretending it is hotter than it is.
        entries = self._entries()
        result = solve_prices.capability_price_for_requirement(
            "thermal_mj", 5000.0, entries,
            {"mechanical_mj": 1.0, "thermal_mj": 1.0}, {"labourer": 1.0})
        self.assertIsNone(result)


class SyntheticFrictionScenarioTests(unittest.TestCase):
    """Reproduces the SHAPE of Complaints/43 with tiny synthetic entries: a
    cheap mechanical_mj source (standing in for a water wheel), a friction
    conversion that wins on running cost alone, and a real fuel that costs
    more per MJ but clears the temperature floor. This exercises `solve`
    itself, not just the helper functions above in isolation, so it is a
    canary that the fix is actually wired into the choice-of-technique
    loop rather than merely present in the file.
    """

    def _entries(self, capped):
        entries = {
            "cheap_shaft": {"outputs": {"mechanical_mj": 1000.0}, "inputs": {},
                            "labour_hours": {"labourer": 0.001},
                            "requires_node": None},
            "friction": {"outputs": {"thermal_mj": 1000.0}, "inputs": {},
                        "labour_hours": {}, "mechanical_mj": 1.0,
                        "requires_node": None},
            "real_fuel": {"outputs": {"thermal_mj": 1000.0}, "inputs": {},
                         "labour_hours": {"labourer": 10.0},
                         "requires_node": None},
        }
        if capped:
            entries["friction"]["temperature_reached_c"] = 100.0
            entries["real_fuel"]["temperature_reached_c"] = 1100.0
        return entries

    def _thermal_choice(self, entries):
        wage_by_trade = {"labourer": 1.0}
        producers_of = solve_prices.build_producers_index(entries)
        resolvable = solve_prices.compute_resolvable_materials(entries, producers_of)
        _prices, _iters, _residual, chosen = solve_prices.solve(
            entries, producers_of, resolvable, wage_by_trade)
        return chosen["thermal_mj"]

    def test_without_any_stated_reach_friction_wins_on_cost_alone(self):
        # Pins the OLD behaviour on these synthetic entries, so the next
        # test's result is legible as "the cap changed this", not "these
        # entries never exercised the choice to begin with".
        self.assertEqual(self._thermal_choice(self._entries(capped=False)), "friction")

    def test_with_a_stated_reach_the_real_fuel_wins_instead(self):
        self.assertEqual(self._thermal_choice(self._entries(capped=True)), "real_fuel")


class RealHeatSourceReachTests(unittest.TestCase):
    def test_thermal_mj_friction_cannot_clear_the_universal_floor(self):
        production_entries, _duplicates = solve_prices.load_production()
        friction = production_entries["thermal_mj_friction"]
        self.assertLess(friction["temperature_reached_c"],
                        solve_prices.THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C)

    def test_charcoal_and_coal_clear_the_universal_floor(self):
        production_entries, _duplicates = solve_prices.load_production()
        for recipe_id in ("thermal_mj_charcoal", "thermal_mj_coal"):
            self.assertGreaterEqual(
                production_entries[recipe_id]["temperature_reached_c"],
                solve_prices.THERMAL_MJ_MINIMUM_USABLE_TEMPERATURE_C)


if __name__ == "__main__":
    unittest.main()
