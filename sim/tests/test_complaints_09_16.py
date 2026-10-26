"""Focused regressions for the second group of playtest complaints, one rule at a time on built inputs (Complaint 640):
which projects a material shortage slows, the sizes of a saltpetre remedy, whether a capability is instantaneous, what a
credit forecast calls its figures, and the help index. The same in a real game is test_complaints_09_16_scenario.
(The money_blocked and money_unfunded waiting causes are held by test_project_pacing and test_scheduling_legibility.)"""
QUICK_TOPIC = True

import types
import unittest

from sim.projects.api import instantaneous
is_instantaneous = instantaneous.is_instantaneous
from sim.materials.rules import input_pools, shared_throttle
from sim.resources.sizing import nitre_bed_square_metres, nitre_deficit_tonnes
from sim.ui.proto import credit_forecast
from sim.ui.proto.help import _agent_help

LAB = "_g"


def pool_of(material):
    return {"saltpetre_kg": "saltpetre", "coal_kg": "coal", "charcoal_kg": "charcoal"}.get(material, "other")


class ProjectThrottle(unittest.TestCase):
    def test_a_nitre_shortage_throttles_a_project_that_consumes_nitre(self):
        pools = input_pools(["saltpetre_kg", "charcoal_kg"], False, pool_of, LAB)
        self.assertEqual(shared_throttle(0.05, "saltpetre", pools), 0.05)

    def test_the_same_shortage_leaves_a_project_with_no_matching_input_at_full_pace(self):
        self.assertEqual(shared_throttle(0.05, "saltpetre", input_pools([], False, pool_of, LAB)), 1.0)
        self.assertEqual(shared_throttle(0.05, "saltpetre", input_pools(["charcoal_kg"], False, pool_of, LAB)), 1.0)

    def test_a_slight_throttle_or_no_binding_pool_slows_nothing(self):
        self.assertEqual(shared_throttle(0.9995, "saltpetre", {"saltpetre"}), 1.0)
        self.assertEqual(shared_throttle(0.05, None, {"saltpetre"}), 1.0)

    def test_a_project_on_coke_draws_coal_in_place_of_charcoal(self):
        self.assertEqual(input_pools(["charcoal_kg"], True, pool_of, LAB), {"coal"})
        self.assertEqual(input_pools(["charcoal_kg"], False, pool_of, LAB), {"charcoal"})

    def test_gram_scale_purchases_never_take_part(self):
        self.assertEqual(input_pools(["saltpetre_g", "saltpetre_kg"], False, lambda material: material, LAB), {"saltpetre_kg"})


class NitreRemedySize(unittest.TestCase):
    YIELD = 0.0008
    BUFFER = 1.2

    def test_the_deficit_is_the_demand_the_beds_market_and_stock_do_not_cover(self):
        self.assertAlmostEqual(nitre_deficit_tonnes(0.0, 1.1, 0.0, self.YIELD, 0.0, 0.0), 1.1)
        self.assertAlmostEqual(nitre_deficit_tonnes(0.0, 1.1, 500.0, self.YIELD, 0.2, 0.1), 1.1 - 0.4 - 0.2 - 0.1)

    def test_a_reported_shortfall_larger_than_the_gap_governs_and_a_surplus_needs_nothing(self):
        self.assertEqual(nitre_deficit_tonnes(2.0, 1.1, 0.0, self.YIELD, 0.0, 0.0), 2.0)
        self.assertEqual(nitre_deficit_tonnes(0.0, 1.1, 5000.0, self.YIELD, 0.0, 0.0), 0.0)

    def test_the_bed_is_sized_from_the_deficit_plus_its_buffer_not_a_fixed_area(self):
        beds = nitre_bed_square_metres(nitre_deficit_tonnes(0.0, 1.1, 0.0, self.YIELD, 0.0, 0.0), self.BUFFER, self.YIELD)
        self.assertGreaterEqual(beds, 1.1 * self.BUFFER / self.YIELD)
        self.assertLess(beds, 1.1 * self.BUFFER / self.YIELD + 100.0)
        self.assertNotEqual(beds, 20000)


class InstantaneousCapability(unittest.TestCase):
    def test_a_capability_with_no_hours_money_labour_or_risk_completes_when_started(self):
        self.assertTrue(is_instantaneous(0.0, 0.0, 0.0, {}, 0.0))

    def test_anything_with_hours_a_calendar_floor_money_labour_or_risk_is_a_project(self):
        for arguments in ((1.0, 0.0, 0.0, {}, 0.0), (0.0, 2.0, 0.0, {}, 0.0), (0.0, 0.0, 10.0, {}, 0.0),
                          (0.0, 0.0, 0.0, {"smith": 5.0}, 0.0), (0.0, 0.0, 0.0, {}, 0.1)):
            self.assertFalse(is_instantaneous(*arguments), arguments)


class CreditForecastLabels(unittest.TestCase):
    RATE = 0.075

    def forecast(self):
        return credit_forecast.borrowing_forecast(900.0, 0.0, 500.0, lambda: 2000.0, lambda: self.RATE, lambda after: {})

    def test_the_percentage_is_labelled_as_a_rate(self):
        self.assertEqual(self.forecast()["interest_rate_percent"], round(self.RATE * 100, 1))

    def test_the_annual_charge_is_the_borrowed_sum_at_that_rate(self):
        forecast = self.forecast()
        self.assertEqual(forecast["estimated_annual_interest"], round(forecast["you_would_borrow"] * self.RATE, 1))
        self.assertEqual(forecast["you_would_borrow"], 400.0)

    def test_the_misleading_old_interest_per_year_field_is_gone(self):
        self.assertNotIn("interest_per_year_on_it", self.forecast())


class CapacityHelp(unittest.TestCase):
    def test_capacity_is_in_the_command_index_and_distinguishes_flow_from_stock(self):
        commands = _agent_help(types.SimpleNamespace(fog=None), "commands")["commands"]
        self.assertIn("capacity", commands)
        # presentation: the help text tells the player flow from durable stock
        for word in ("throughput", "stock", "materials"):
            self.assertIn(word, commands["capacity"])


if __name__ == "__main__":
    unittest.main()
