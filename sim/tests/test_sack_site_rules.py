"""The hazards module's sack_site on a household of plain figures: the people the sack announces are the people the headcount
loses, hired staff included, and the corpus roll that follows is made against the hedge in force."""

QUICK_TOPIC = True

import itertools
import types
import unittest

from sim.reporting.api import RecordEvent
from sim.tests import hazards_host, module_harness
from sim.workforce.api import SurviveStaff
from sim.workforce.module import Workforce


class AlternatingDice:
    """random() alternates a low and a high draw, so about half of any headcount survives."""

    def __init__(self):
        self.draws = itertools.cycle([0.0, 0.9])

    def random(self):
        return next(self.draws)


class SackedHousehold:
    """A household, the dice, and the hazards module over them: a SurviveStaff it sends thins the household as the workforce module does."""

    def __init__(self, corpus_chance=0.0):
        self.dice = AlternatingDice()
        self.household = types.SimpleNamespace(artisans=20.0, scholars=10.0, directors_extra=5.0, capital=1000.0,
                                               employees={"smith": 40.0, "scribe": 30.0, "mason": 20.0})
        workforce = module_harness.build(Workforce, seat=self.household, views={"legacy_acting_household": self.household, "legacy_dice": self.dice})
        self.module = hazards_host.build(
            legacy_dice=self.dice, staff=lambda: {"scholars": self.household.scholars, "artisans": self.household.artisans,
                                                  "employees": self.household.employees},
            acting_balance=lambda: self.household.capital, corpus_hedge=(corpus_chance, 0.5, "corpus_written"),
            answers={SurviveStaff: workforce.survive_staff})
        self.corpus_loss_asked = []
        self.module.sack_corpus_loss = lambda year, fraction, hedge: self.corpus_loss_asked.append((year, fraction, hedge))

    def people(self):
        household = self.household
        return household.artisans + household.scholars + sum(household.employees.values())

    def sack(self):
        self.module.sack_site({"name": "TEST"}, 100)

    def lines(self):
        return [command for command in module_harness.sent(self.module) if isinstance(command, RecordEvent)]


class SackSite(unittest.TestCase):

    def test_the_people_announced_gone_are_the_fall_in_total_headcount(self):
        game = SackedHousehold()
        before = game.people()
        game.sack()
        line, = game.lines()
        self.assertEqual(line.kind, "site_sacked")
        self.assertGreater(line.facts["people_gone"], 0.0)
        self.assertAlmostEqual(line.facts["people_gone"], before - game.people(), places=2)

    def test_hired_staff_are_among_those_lost(self):
        game = SackedHousehold()
        before = sum(game.household.employees.values())
        game.sack()
        self.assertLess(sum(game.household.employees.values()), before)

    def test_a_corpus_loss_is_rolled_only_when_the_hedge_chance_is_met(self):
        sure = SackedHousehold(corpus_chance=1.0)
        sure.sack()
        self.assertEqual(sure.corpus_loss_asked, [(100, 0.5, "corpus_written")])
        never = SackedHousehold(corpus_chance=0.0)
        never.sack()
        self.assertEqual(never.corpus_loss_asked, [])


if __name__ == "__main__":
    unittest.main()
