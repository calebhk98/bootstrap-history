"""Complaint 640: how a household's log and projects show the credit warnings and the halt. `CreditMixin.warn_near_the_limit` and
`answer_exhausted_credit` run on a stand-in game; the warning band and the halt itself are test_credit_warning_rules."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.engine.economy_credit import CreditMixin
from sim.refusal import cause_of, facts_of
from sim.tests import event_stand_in

LIMIT = 1000.0


class Owing:
    """A household owing `share` of its credit limit, with projects in hand."""
    send = event_stand_in.send

    CREDIT_FREEZE_YEARS_AFTER_HALT = 5
    HOUSEHOLD_DISPERSAL_ARTISANS_FLOOR = 1.0
    HOUSEHOLD_DISPERSAL_ARTISANS_RETENTION = 0.4

    def __init__(self, share, slaves=0, closures=()):
        self.state = SimpleNamespace(
            household=SimpleNamespace(capital=-share * LIMIT, log=[], _said_near_limit=False, credit_frozen_until=0, slaves=slaves, freedmen=0, artisans=10.0),
            projects=SimpleNamespace(active={"a_project": {"spent": 40.0}}, bountied=set(), paid_towards={}),
            scenario=SimpleNamespace(year=100))
        self.closures, self.mothballed, self.manumitted = list(closures), [], []
        self.labour = SimpleNamespace(manumit=self.manumitted.append)
        self.civ = {"id": "rome_100ad"}

    def credit_limit(self):
        return LIMIT

    def mothball_mines(self):
        self.mothballed.append(True)

    def review_ventures(self, rules, year):
        return [SimpleNamespace(entry_key=key) for key in self.closures]


def kinds(game):
    return [cause_of(line) for _year, line in game.state.household.log]


# ---- the warning
game = Owing(0.8)
CreditMixin.warn_near_the_limit(game, 100)
CreditMixin.warn_near_the_limit(game, 101)
check("the warning is logged once while in the band", kinds(game) == ["credit_near_limit"], kinds(game))
check("the warning's fact is the share of the limit used", abs(facts_of(game.state.household.log[0][1])["share_of_limit"] - 0.8) < 1e-9, None)
game.state.household.capital = 0.0
CreditMixin.warn_near_the_limit(game, 102)
game.state.household.capital = -0.8 * LIMIT
CreditMixin.warn_near_the_limit(game, 103)
check("the warning is given again after the household recovers", kinds(game).count("credit_near_limit") == 2, kinds(game))
game = Owing(0.3)
CreditMixin.warn_near_the_limit(game, 100)
check("far from the limit there is no warning", kinds(game) == [], None)

# ---- past the limit
game = Owing(1.5)
CreditMixin.answer_exhausted_credit(game, 100)
check("past the limit work in hand stops, and what was paid stands to its credit", game.state.projects.active == {} and game.state.projects.paid_towards == {"a_project": 40.0},
      game.state.projects)
check("credit freezes for the declared years", game.state.household.credit_frozen_until == 105, game.state.household.credit_frozen_until)
check("the line says so by kind and names what stopped", kinds(game) == ["credit_exhausted"] and facts_of(game.state.household.log[0][1])["stopped"] == ["a_project"]
      and facts_of(game.state.household.log[0][1])["frozen_until"] == 105, game.state.household.log)
check("still past the limit the mines are mothballed", game.mothballed == [True], None)
game = Owing(1.5, closures=["plant_a", "plant_b"])
CreditMixin.answer_exhausted_credit(game, 100)
check("what creditors seize is logged by kind", "creditors_took" in kinds(game), kinds(game))
game = Owing(1.5)
CreditMixin.answer_exhausted_credit(game, 100)
check("when nothing is seized nothing is said of it", "creditors_took" not in kinds(game), kinds(game))
game = Owing(1.5, slaves=30)
CreditMixin.answer_exhausted_credit(game, 100)
check("a household that cannot feed its people disperses them", "household_disperses" in kinds(game) and game.manumitted == [30] and game.state.household.artisans == 4.0, kinds(game))
game = Owing(0.5)
CreditMixin.answer_exhausted_credit(game, 100)
check("inside the limit nothing is stopped, frozen or said", "a_project" in game.state.projects.active and kinds(game) == [] and game.mothballed == []
      and game.state.household.credit_frozen_until == 0, kinds(game))
