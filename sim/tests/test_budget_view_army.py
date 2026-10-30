"""`BudgetView` army readings: the force a state wants is its civilisation's opening force raised by the sack hazards running that
year, and does not read the head count; the soldiers kept now are last year's paid force, else the force wanted. Called on a
stand-in `self` carrying only the civilisation and year."""

QUICK_TOPIC = True

from types import SimpleNamespace
import unittest

from sim.agents.budget import army_goal
from sim.actors.world_budget import BudgetView

from .world_stand_in import fake_needs

HAZARDS = [{"years": [100, 150], "sack_chance": 0.1}, {"years": [200, 250], "sack_chance": 0.0}]


def view(year, opening=1000.0, hazards=HAZARDS, kept=0.0):
    stand_in = SimpleNamespace(year=year, needs=fake_needs(civilisation={"standing_army": opening, "hazards": hazards}),
                               government=lambda: SimpleNamespace(record=SimpleNamespace(army=kept)))
    stand_in.threat_pressure = lambda: BudgetView.threat_pressure(stand_in)
    stand_in.army_wanted = lambda: BudgetView.army_wanted(stand_in)
    return stand_in


class ArmyWanted(unittest.TestCase):
    def test_a_sack_hazard_running_that_year_raises_the_force_over_the_opening_one(self):
        self.assertEqual(BudgetView.army_wanted(view(year=120)), army_goal(1000.0, 0.1))
        self.assertGreater(BudgetView.army_wanted(view(year=120)), 1000.0)

    def test_a_year_with_no_sack_hazard_wants_the_opening_force(self):
        self.assertEqual(BudgetView.army_wanted(view(year=225)), 1000.0)
        self.assertEqual(BudgetView.army_wanted(view(year=175)), 1000.0)

    def test_a_civilisation_that_opens_with_no_standing_force_wants_none(self):
        self.assertEqual(BudgetView.army_wanted(view(year=120, opening=0.0)), 0.0)

    def test_the_threat_is_the_sack_chances_of_the_hazards_running(self):
        self.assertEqual(BudgetView.threat_pressure(view(year=120)), 0.1)
        self.assertEqual(BudgetView.threat_pressure(view(year=300)), 0.0)


class SoldiersUnderArms(unittest.TestCase):
    def test_last_years_paid_force_is_the_force_kept(self):
        self.assertEqual(BudgetView.soldiers_under_arms(view(year=120, kept=640.0)), 640.0)

    def test_with_none_kept_it_is_the_force_wanted(self):
        self.assertEqual(BudgetView.soldiers_under_arms(view(year=225, kept=0.0)), 1000.0)


if __name__ == "__main__":
    unittest.main()
