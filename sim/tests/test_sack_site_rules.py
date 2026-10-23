"""_sack_site on a stand-in household: the people the sack announces are the people the headcount loses, hired staff
included, and the corpus roll that follows is made against the hedge in force."""

QUICK_TOPIC = True

import itertools
import types
import unittest

from sim.engine.society_hazards import HazardsMixin
from sim.refusal import cause_of, facts_of


class AlternatingDice:
    """random() alternates a low and a high draw, so about half of any headcount survives."""

    def __init__(self):
        self.draws = itertools.cycle([0.0, 0.9])
        self.corpus_rolls = 0

    def random(self):
        return next(self.draws)


class SackedHousehold(HazardsMixin):
    """Only what a sack reads: the household, the projects, the labour book and the corpus hedge."""

    def __init__(self, corpus_chance=0.0):
        self.rng = AlternatingDice()
        self.civ = {}
        self.nodes = {}
        self.corpus_chance = corpus_chance
        self.corpus_loss_asked = []
        self.state = types.SimpleNamespace(
            household=types.SimpleNamespace(artisans=20.0, scholars=10.0, directors_extra=5.0, capital=1000.0, log=[],
                                            employees={"smith": 40.0, "scribe": 30.0, "mason": 20.0}),
            projects=types.SimpleNamespace(active={}))
        self.labour = types.SimpleNamespace(staff_snapshot=lambda: {}, log_staff_reduction=lambda name, before: None)

    def plunder_founder(self, strength, reason, order_holds=True):
        pass

    def corpus_hedge(self):
        return self.corpus_chance, 0.5, "corpus_written"

    def _sack_corpus_loss(self, year, frac, hedge):
        self.corpus_loss_asked.append((year, frac, hedge))

    def people(self):
        household = self.state.household
        return household.artisans + household.scholars + sum(household.employees.values())


class SackSite(unittest.TestCase):

    def test_the_people_announced_gone_are_the_fall_in_total_headcount(self):
        game = SackedHousehold()
        before = game.people()
        game._sack_site({"name": "TEST"}, 100)
        (_year, line), = game.state.household.log
        self.assertEqual(cause_of(line), "site_sacked")
        self.assertGreater(facts_of(line)["people_gone"], 0.0)
        self.assertAlmostEqual(facts_of(line)["people_gone"], before - game.people(), places=2)

    def test_hired_staff_are_among_those_lost(self):
        game = SackedHousehold()
        before = sum(game.state.household.employees.values())
        game._sack_site({"name": "TEST"}, 100)
        self.assertLess(sum(game.state.household.employees.values()), before)

    def test_a_corpus_loss_is_rolled_only_when_the_hedge_chance_is_met(self):
        sure = SackedHousehold(corpus_chance=1.0)
        sure._sack_site({"name": "TEST"}, 100)
        self.assertEqual(sure.corpus_loss_asked, [(100, 0.5, "corpus_written")])
        never = SackedHousehold(corpus_chance=0.0)
        never._sack_site({"name": "TEST"}, 100)
        self.assertEqual(never.corpus_loss_asked, [])


if __name__ == "__main__":
    unittest.main()
