"""`society_techs`, the actors' view of what the society holds: the acting seat's granted techniques plus what the firms and the
government of the cast have learnt. One view over a written-out cast."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.actors.module import Actors
from sim.agents.api import ActorsState
from sim.tests import module_harness


def actor(kind, knowledge, exited=None):
    return SimpleNamespace(kind=kind, knowledge=set(knowledge), record=SimpleNamespace(exited_year=exited))


def actors_over(cast_actors, granted, recorded=True):
    module = module_harness.build(Actors, world=ActorsState(home_country="rome"), module_id="actors",
                                  views={"techniques_granted": granted})
    module.cast_recorded = lambda: recorded
    module.cast = lambda: SimpleNamespace(of_kind=lambda kind: [found for found in cast_actors if found.kind == kind])
    return module


class SocietyTechs(unittest.TestCase):
    def test_the_granted_techniques_and_what_firms_and_the_government_learnt(self):
        module = actors_over([actor("firm", {"loom"}), actor("government", {"coin"}), actor("household", {"steam"})], {"fire"})
        self.assertEqual(module.society_techs(), frozenset({"fire", "loom", "coin"}))

    def test_a_firm_that_has_left_holds_nothing_for_the_society(self):
        module = actors_over([actor("firm", {"kiln"}, exited=1700)], {"fire"})
        self.assertEqual(module.society_techs(), frozenset({"fire"}))

    def test_before_the_cast_has_any_record_only_the_granted_techniques_count(self):
        module = actors_over([actor("firm", {"loom"})], {"fire"}, recorded=False)
        self.assertEqual(module.society_techs(), frozenset({"fire"}))


if __name__ == "__main__":
    unittest.main()
