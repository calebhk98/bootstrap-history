"""A grade of heat no held technique supplies is unavailable, not priced at a technique nobody holds
(Complaints/38). Heat cannot be imported, so a line that needs it cannot run. Small fixtures only."""

QUICK_TOPIC = True

import unittest

from sim.engine import energy_prices, node_output


def _heat_entry(reaches):
    return {"outputs": {"thermal_mj": 1.0}, "inputs": {}, "labour_hours": {"labourer": 1.0},
            "temperature_reached_c": reaches}


def _kiln_entry(needs):
    return {"outputs": {"brick_kg": 1.0}, "inputs": {}, "labour_hours": {"labourer": 1.0},
            "thermal_mj": 2.0, "temperature_needed_c": needs}


class GradeBandsTests(unittest.TestCase):

    def setUp(self):
        self.entries = {"wood": _heat_entry(900.0), "kiln_cool": _kiln_entry(800.0),
                        "kiln_hot": _kiln_entry(1500.0)}
        self.bands, self.hour_bands, self.unreachable = energy_prices.grade_bands(
            self.entries, {"wood": self.entries["wood"]}, {}, {"labourer": 1.0}, 2.0, 0.0)

    def test_a_grade_a_held_technique_reaches_is_priced(self):
        self.assertIn(("thermal_mj", 800.0), self.bands)
        self.assertGreater(self.bands[("thermal_mj", 800.0)], 0.0)

    def test_a_grade_no_held_technique_reaches_has_no_price(self):
        self.assertNotIn(("thermal_mj", 1500.0), self.bands)
        self.assertEqual(self.unreachable, frozenset({("thermal_mj", 1500.0)}))

    def test_with_a_hotter_technique_held_the_grade_is_priced(self):
        entries = dict(self.entries, furnace=_heat_entry(1800.0))
        bands, _hours, unreachable = energy_prices.grade_bands(
            entries, {"furnace": entries["furnace"]}, {}, {"labourer": 1.0}, 2.0, 0.0)
        self.assertIn(("thermal_mj", 1500.0), bands)
        self.assertFalse(unreachable)


class LineNeedingUnreachableHeatTests(unittest.TestCase):

    def setUp(self):
        self.energy = energy_prices.EnergyPrices({"thermal_mj": 1.0}, {("thermal_mj", 800.0): 1.0}, None,
                                                 unreachable={("thermal_mj", 1500.0)})

    def test_an_entry_that_needs_it_cannot_run_and_one_that_does_not_can(self):
        self.assertFalse(self.energy.can_run(_kiln_entry(1500.0)))
        self.assertTrue(self.energy.can_run(_kiln_entry(800.0)))
        self.assertTrue(self.energy.can_run({"outputs": {"cloth_kg": 1.0}}))

    def test_a_node_whose_only_line_needs_it_makes_nothing(self):
        goods = {"brick_kg": 10.0, "thermal_mj": 1.0}
        node = {"id": "kiln_works", "sch": 1.0, "art": 0.0}
        hot, cool = _kiln_entry(1500.0), _kiln_entry(800.0)
        self.assertIsNone(node_output.output_baskets(node, {}, goods, self.energy, entries=[hot]))
        self.assertIsNotNone(node_output.output_baskets(node, {}, goods, self.energy, entries=[cool]))

    def test_pool_only_prices_leave_every_line_runnable(self):
        self.assertTrue(energy_prices.pool_only({"thermal_mj": 1.0}).can_run(_kiln_entry(1500.0)))


if __name__ == "__main__":
    unittest.main()
