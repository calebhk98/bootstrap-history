"""The army a state wants is its civilisation's opening force raised by the sack chance of the hazards running that year.
The world is a stand-in holding only the civilisation record and the year; no game."""

QUICK_TOPIC = True

import types
import unittest

from sim.agents.api import army_goal
from sim.actors.world import ActorWorld
from sim.tests.world_stand_in import fake_needs

OPENING = 4000.0
HAZARDS = [{"sack_chance": 0.1, "years": [200, 260]}, {"years": [0, 999]}]


def world_in(year, hazards=HAZARDS):
    needs = fake_needs(civilisation={"standing_army": OPENING, "hazards": hazards}, year=year)
    return ActorWorld(types.SimpleNamespace(needs=needs))


class ArmyWantedTests(unittest.TestCase):
    def test_with_no_sack_hazard_running_the_state_wants_its_opening_force(self):
        self.assertEqual(world_in(120).army_wanted(), OPENING)

    def test_while_a_sack_hazard_runs_the_state_wants_the_goal_for_that_pressure(self):
        world = world_in(240)
        self.assertAlmostEqual(world.threat_pressure(), 0.1)
        self.assertEqual(world.army_wanted(), army_goal(OPENING, 0.1))
        self.assertGreater(world.army_wanted(), world_in(120).army_wanted())

    def test_a_civilisation_that_declares_no_hazard_never_raises_its_army(self):
        self.assertEqual(world_in(240, hazards=[]).army_wanted(), OPENING)
