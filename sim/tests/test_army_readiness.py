"""Complaint 485, readiness: drill and morale wear down in a peace, battle restores them, and the battle rule reads them.
Each test calls one plain function."""

QUICK_TOPIC = True

import unittest

from sim.world import army_readiness, battle, campaign_contest, military_logistics
from sim.world.army_record import Army

REFERENCE_KG = military_logistics.annual_iron_and_ammunition_burden_kg_per_soldier()


class ReadinessTests(unittest.TestCase):

    def test_an_idle_year_wears_readiness_down_toward_the_floor_and_never_below(self):
        readiness = 1.0
        for _ in range(500):
            after = army_readiness.readiness_after_year(readiness, False)
            self.assertLessEqual(after, readiness)
            readiness = after
        self.assertAlmostEqual(readiness, army_readiness.READINESS_FLOOR, places=6)
        self.assertGreaterEqual(army_readiness.readiness_after_year(0.0, False), army_readiness.READINESS_FLOOR)

    def test_a_year_of_fighting_restores_readiness(self):
        self.assertEqual(army_readiness.readiness_after_year(army_readiness.READINESS_FLOOR, True), 1.0)

    def test_strength_is_scaled_by_readiness(self):
        full = battle.effective_strength(1000.0, REFERENCE_KG, REFERENCE_KG, 1.0, 1.0, 1.0)
        self.assertAlmostEqual(battle.effective_strength(1000.0, REFERENCE_KG, REFERENCE_KG, 1.0, 1.0, 0.5), 0.5 * full)

    def test_a_force_of_armies_has_the_readiness_of_its_men_by_head(self):
        drilled = Army("a", "o", "t", 300.0, REFERENCE_KG)
        stale = Army("b", "o", "t", 100.0, REFERENCE_KG, readiness=0.4)
        self.assertAlmostEqual(campaign_contest.combine([drilled, stale]).readiness, (300.0 * 1.0 + 100.0 * 0.4) / 400.0)

    def test_readiness_is_kept_in_the_army_record(self):
        self.assertEqual(Army.from_dict(Army("a", "o", "t", 10.0, 1.0, readiness=0.7).to_dict()).readiness, 0.7)


if __name__ == "__main__":
    unittest.main()
