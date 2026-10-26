"""What the yearly staffing reopening does with the plants the business's review brings back
(`StaffingMixin.reopen_restaffed_ventures`): the count is recorded as staffing reopenings and the household's log says it, naming
at most four and counting those still shut. Which plants come back is `business_review.reopen`, in test_arrears_hours. The
mixin runs on a stand-in, with the review and the world adapter replaced by recorders."""

QUICK_TOPIC = True

from types import SimpleNamespace
from unittest import mock

from .harness import check

from sim.engine import projects_staffing
from sim.engine.projects_staffing import StaffingMixin
from sim.refusal import cause_of, facts_of
from sim.tests import event_stand_in


class Game(StaffingMixin):
    """The parts of a Sim a reopening touches."""
    send = event_stand_in.send

    def __init__(self, reopened, still_shut=2):
        self.asked = []
        self.recorded = []
        self.household = "household-adapter"
        self.state = SimpleNamespace(household=SimpleNamespace(log=[]), scenario=SimpleNamespace(year=100), projects=SimpleNamespace(
            business=SimpleNamespace(review_reopening=lambda household, world: self.asked.append((household, world)) or reopened)))
        self.still_shut = still_shut

    def view(self, name):
        return lambda: ("world-of", self)

    def record_staffing_reopenings(self, count):
        self.recorded.append(count)

    def staffing_shut_count(self):
        return self.still_shut


def reopen(reopened, **keywords):
    game = Game(reopened, **keywords)
    result = game.reopen_restaffed_ventures(130)
    return game, result


game, result = reopen({"b", "a"})
check("the review is asked with the game's household and a world over the game", game.asked == [("household-adapter", ("world-of", game))])
check("the plants the review reopened are returned and counted", result == {"a", "b"} and game.recorded == [2], (result, game.recorded))
lines = game.state.household.log
check("the household's log has one concerns_reopened line for the year", [(year, cause_of(line)) for year, line in lines] == [(130, "concerns_reopened")], lines)
check("the line's facts are the plants reopened, in order, and the count still shut",
      facts_of(lines[0][1]) == {"reopened": ["a", "b"], "still_shut": 2}, facts_of(lines[0][1]))
game, _ = reopen({"only"}, still_shut=0)
check("a single plant is a list of one with none still shut",
      facts_of(game.state.household.log[0][1]) == {"reopened": ["only"], "still_shut": 0})
game, _ = reopen({"p5", "p3", "p1", "p4", "p2"})
check("every plant reopened is in the facts and all are counted",
      facts_of(game.state.household.log[0][1])["reopened"] == ["p1", "p2", "p3", "p4", "p5"] and game.recorded == [5])
game, result = reopen(set())
check("when nothing reopens nothing is recorded or said", result == set() and game.recorded == [] and game.state.household.log == [])
