"""Complaint 640: how a household's log and projects show the credit warnings and the halt. The finance module's `warn_near_the_limit`
and `answer_exhausted_credit` run over plain values for the views they read; the warning band and the halt itself are
test_credit_warning_rules."""

QUICK_TOPIC = True

from sim.tests import workforce_stand_in
from types import SimpleNamespace

from .harness import check

from sim.projects.api import HaltActiveProjects, ReviewVentures, halt_active_projects
from sim.reporting.api import RecordEvent
from sim.resources.api import MothballMines
from sim.tests import finance_host, module_harness
from sim.workforce.api import Manumit

LIMIT = 1000.0


class Owing:
    """A household owing `share` of its credit limit, with projects in hand."""

    def __init__(self, share, slaves=0, closures=()):
        self.household = SimpleNamespace(capital=-share * LIMIT, slaves=slaves, freedmen=0, artisans=10.0, scholars=0)
        self.projects = SimpleNamespace(active={"a_project": {"spent": 40.0}}, bountied=set(), paid_towards={})
        self.manumitted = []
        answers = {
            ReviewVentures: lambda command: [SimpleNamespace(entry_key=key) for key in closures],
            Manumit: lambda command: self.manumitted.append(command.people),
            # the projects module's own rule over the stand-in record
            HaltActiveProjects: lambda command: halt_active_projects(self.projects.active, self.projects.paid_towards, self.projects.bountied) if self.projects.active else ([], 0.0)}
        self.module = finance_host.build(answers=answers, household=self.household)
        self.module.credit_limit = lambda revenue=None, upkeep=None, capital=None: LIMIT

    @property
    def events(self):
        return [command for command in module_harness.sent(self.module) if isinstance(command, RecordEvent)]

    @property
    def kinds(self):
        return [event.kind for event in self.events]

    @property
    def mothballed(self):
        return [command for command in module_harness.sent(self.module) if isinstance(command, MothballMines)]


# ---- the warning
game = Owing(0.8)
game.module.warn_near_the_limit(100)
game.module.warn_near_the_limit(101)
check("the warning is logged once while in the band", game.kinds == ["credit_near_limit"], game.kinds)
check("the warning's fact is the share of the limit used", abs(game.events[0].facts["share_of_limit"] - 0.8) < 1e-9, None)
game.household.capital = 0.0
game.module.warn_near_the_limit(102)
game.household.capital = -0.8 * LIMIT
game.module.warn_near_the_limit(103)
check("the warning is given again after the household recovers", game.kinds.count("credit_near_limit") == 2, game.kinds)
game = Owing(0.3)
game.module.warn_near_the_limit(100)
check("far from the limit there is no warning", game.kinds == [], None)

# ---- past the limit
game = Owing(1.5)
game.module.answer_exhausted_credit(100)
check("past the limit work in hand stops, and what was paid stands to its credit", game.projects.active == {} and game.projects.paid_towards == {"a_project": 40.0},
      game.projects)
check("credit freezes for the declared years", game.module.seat.credit_frozen_until == 105, game.module.seat.credit_frozen_until)
check("the line says so by kind and names what stopped", game.kinds == ["credit_exhausted"] and game.events[0].facts["stopped"] == ["a_project"]
      and game.events[0].facts["frozen_until"] == 105, game.events)
check("still past the limit the mines are mothballed", len(game.mothballed) == 1, None)
game = Owing(1.5, closures=["plant_a", "plant_b"])
game.module.answer_exhausted_credit(100)
check("what creditors seize is logged by kind", "creditors_took" in game.kinds, game.kinds)
game = Owing(1.5)
game.module.answer_exhausted_credit(100)
check("when nothing is seized nothing is said of it", "creditors_took" not in game.kinds, game.kinds)
game = Owing(1.5, slaves=30)
game.module.answer_exhausted_credit(100)
check("a household that cannot feed its people disperses them", "household_disperses" in game.kinds and game.manumitted == [30]
      and game.household.artisans == 4.0, game.kinds)
game = Owing(0.5)
game.module.answer_exhausted_credit(100)
check("inside the limit nothing is stopped, frozen or said", "a_project" in game.projects.active and game.kinds == [] and game.mothballed == []
      and game.module.seat.credit_frozen_until == 0, game.kinds)
