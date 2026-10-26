"""The goal screen's system levers (Complaint 98), called on a stand-in game that answers the figures each lever reads."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.ui.proto.guidance import leverage_points


def stand_in_game():
    labour = SimpleNamespace(director_pool=lambda: 123.456, director_hours_committed=lambda: 40.04,
                             supervision_room=lambda: 7.77)
    return SimpleNamespace(
        labour=labour, operating={"mill": 1, "forge": 2},
        view=lambda name: {"material_throttle": lambda: 0.4567, "material_binding": lambda: "iron"}[name],
        literacy=lambda kind: 0.25, literacy_ceiling_general=lambda: 0.8, effective_schooling_flow=lambda: 0.0123,
        recurring_net=lambda: -55.55, credit_limit=lambda: 900.0, spending_power=lambda mode: 321.0,
        knowledge_risk=lambda **options: {"technologies_at_risk": 3, "expected_technologies_lost_per_sacking": 0.5})


class LeveragePoints(unittest.TestCase):
    def setUp(self):
        self.points = {point["lever"]: point for point in leverage_points(stand_in_game())}

    def test_the_levers_are_literacy_labour_finance_institutions_knowledge_and_materials(self):
        self.assertEqual(list(self.points), ["literacy", "labour", "finance", "institutions", "knowledge", "materials"])

    def test_every_lever_carries_figures_and_what_it_unlocks(self):
        for point in self.points.values():
            self.assertTrue(point["figures"] and point["why_it_matters"], point)

    def test_labour_reads_the_directed_hour_pool_and_supervision_room(self):
        self.assertEqual(self.points["labour"]["figures"],
                         {"directed_hours_this_year": 123.5, "committed_hours": 40.0, "people_you_can_oversee": 7.8})

    def test_finance_reads_the_recurring_net_credit_and_spending_power(self):
        self.assertEqual(self.points["finance"]["figures"],
                         {"recurring_net_per_year": -55.5, "credit_limit": 900.0, "you_could_raise_now": 321.0})

    def test_literacy_and_materials_read_the_engine(self):
        self.assertEqual(self.points["literacy"]["figures"],
                         {"literacy_general": 0.25, "general_ceiling": 0.8, "schooling_flow": 0.012})
        self.assertEqual(self.points["materials"]["figures"], {"work_runs_at_share_of_plan": 0.457, "binding_material": "iron"})

    def test_institutions_count_the_running_concerns_and_knowledge_reads_the_risk(self):
        self.assertEqual(self.points["institutions"]["figures"]["concerns_running"], 2)
        self.assertEqual(self.points["knowledge"]["figures"],
                         {"technologies_at_risk": 3, "expected_lost_per_sacking": 0.5})


if __name__ == "__main__":
    unittest.main()
