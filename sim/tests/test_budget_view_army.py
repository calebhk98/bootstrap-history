"""`Army` readings of the home world: the force a state wants is its civilisation's opening force raised by the sack hazards running that
year, and does not read the head count; the soldiers kept now are last year's paid force, else the force wanted. Called on the part over a
stand-in world carrying only the civilisation and year."""

QUICK_TOPIC = True

from types import SimpleNamespace
import unittest

from sim.agents.budget import army_goal
from sim.actors.world_army import Army

from .world_stand_in import fake_needs

HAZARDS = [{"years": [100, 150], "sack_chance": 0.1}, {"years": [200, 250], "sack_chance": 0.0}]


def view(year, opening=1000.0, hazards=HAZARDS, kept=0.0):
    stand_in = SimpleNamespace(needs=fake_needs(civilisation={"standing_army": opening, "hazards": hazards}),
                               setting=SimpleNamespace(year=year, government=lambda: SimpleNamespace(record=SimpleNamespace(army=kept))))
    return Army(stand_in)


class ArmyWanted(unittest.TestCase):
    def test_a_sack_hazard_running_that_year_raises_the_force_over_the_opening_one(self):
        self.assertEqual(view(year=120).army_wanted(), army_goal(1000.0, 0.1))
        self.assertGreater(view(year=120).army_wanted(), 1000.0)

    def test_a_year_with_no_sack_hazard_wants_the_opening_force(self):
        self.assertEqual(view(year=225).army_wanted(), 1000.0)
        self.assertEqual(view(year=175).army_wanted(), 1000.0)

    def test_a_civilisation_that_opens_with_no_standing_force_wants_none(self):
        self.assertEqual(view(year=120, opening=0.0).army_wanted(), 0.0)

    def test_the_threat_is_the_sack_chances_of_the_hazards_running(self):
        self.assertEqual(view(year=120).threat_pressure(), 0.1)
        self.assertEqual(view(year=300).threat_pressure(), 0.0)


class SoldiersUnderArms(unittest.TestCase):
    def test_last_years_paid_force_is_the_force_kept(self):
        self.assertEqual(view(year=120, kept=640.0).soldiers_under_arms(), 640.0)

    def test_with_none_kept_it_is_the_force_wanted(self):
        self.assertEqual(view(year=225, kept=0.0).soldiers_under_arms(), 1000.0)


if __name__ == "__main__":
    unittest.main()
