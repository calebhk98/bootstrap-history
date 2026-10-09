"""Mine works charged besides breaking: barren rock, haulage, hoisting,
drainage, timbering, ventilation (Complaints/348)."""

QUICK_TOPIC = True

import unittest

from sim.world import deposits, mine_fire_setting, mine_works

# Bettenay 2022 (Metalla 26.2): face miners and fire-setters are 40-70
# percent of mine staff, the rest underground or surface support.
FACE_SHARE_OF_MINE_STAFF_RANGE = (0.4, 0.7)


def _probe(depth_class, hardness_class="medium"):
    return deposits.Deposit(
        name="probe", metal="test", tile="nowhere", material_moved="ore",
        ore_grade_kg_per_tonne=10.0, depth_class=depth_class,
        hardness_class=hardness_class, quantity_tonnes_per_year=100.0, note="")


def _terms(deposit):
    return mine_works.works_hours_per_tonne_ore(
        deposit.depth_class, deposit.hardness_class,
        deposits._lift_hours_per_tonne_metre(),
        deposits.shaft_depth_metres(deposit), mine_fire_setting.MINING_SHIFT_HOURS,
        drainage_hours_per_tonne_metre=deposits.drainage_lift_hours_per_tonne_metre())


class MineWorks(unittest.TestCase):

    def test_underground_ore_carries_barren_rock(self):
        for depth_class in ("shallow_vein", "deep_vein"):
            self.assertGreater(mine_works.rock_broken_tonnes_per_tonne_ore(depth_class), 1.0)

    def test_every_term_is_charged_underground_and_none_is_negative(self):
        terms = _terms(_probe("deep_vein", "hard"))
        for name, hours in terms.items():
            self.assertGreater(hours, 0.0, name)

    def test_deeper_costs_more_per_tonne(self):
        self.assertGreater(deposits.vein_hours_per_tonne_ore(_probe("deep_vein")),
                           deposits.vein_hours_per_tonne_ore(_probe("shallow_vein")))
        self.assertGreater(deposits.vein_hours_per_tonne_ore(_probe("shallow_vein")),
                           deposits.vein_hours_per_tonne_ore(_probe("surface")))

    def test_hoisting_is_the_physical_lift_of_a_tonne_from_depth(self):
        deposit = _probe("deep_vein")
        expected = (9.81 * 1000.0 * deposits.shaft_depth_metres(deposit)
                    / (deposits.HUMAN_SUSTAINED_POWER_WATTS
                       * deposits.HOIST_MECHANICAL_EFFICIENCY * 3600.0))
        self.assertAlmostEqual(_terms(deposit)["hoist"], expected, places=6)

    def test_support_work_of_a_deep_mine_is_within_the_source_staffing_split(self):
        # support hours per face hour = (1 - face share) / face share. The
        # shallow class falls just under the source's low end (Complaints/349).
        deposit = _probe("deep_vein", "hard")
        support = sum(_terms(deposit).values())
        rock_per_ore = mine_works.rock_broken_tonnes_per_tonne_ore("deep_vein")
        face = ((deposits.BREAKING_HOURS_PER_TONNE_HARD
                 + mine_fire_setting.fire_setting_labour_hours_per_tonne_rock("hard"))
                * rock_per_ore)
        low, high = FACE_SHARE_OF_MINE_STAFF_RANGE
        self.assertGreaterEqual(support / face, (1 - high) / high)
        self.assertLessEqual(support / face, (1 - low) / low)

    def test_ventilation_shaft_adds_to_the_shaft_build(self):
        deposit = _probe("deep_vein", "hard")
        with_vent = deposits.shaft_cost_labour_hours(deposit)
        saved = mine_works.VENTILATION_OPENINGS_PER_WORKING_SHAFT
        mine_works.VENTILATION_OPENINGS_PER_WORKING_SHAFT = 0.0
        try:
            without = deposits.shaft_cost_labour_hours(deposit)
        finally:
            mine_works.VENTILATION_OPENINGS_PER_WORKING_SHAFT = saved
        self.assertGreater(with_vent, without)

    def test_alluvial_ground_is_not_charged_vein_works(self):
        self.assertEqual(deposits.extraction_cost_labour_hours_per_kg(_probe("alluvial")),
                         deposits.ALLUVIAL_HAND_PROCESSING_HOURS_PER_TONNE / 10.0)

    def test_shift_is_agricolas_seven_hours(self):
        self.assertEqual(mine_fire_setting.MINING_SHIFT_HOURS, 7.0)


if __name__ == "__main__":
    unittest.main()
