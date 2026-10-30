"""What the yearly staffing reopening does with the plants the business's review brings back
(the projects module's `reopen_restaffed_ventures`): the count is recorded as staffing reopenings and the household's log says it,
naming at most four and counting those still shut. Which plants come back is `business_review.reopen`, in test_arrears_hours. The
module runs over plain values, the ventures module's answer to the review replaced by a recorder."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.reporting.api import RecordEvent
from sim.ventures.api import ReviewReopening
from sim.tests import module_harness, projects_host


def Game(reopened, still_shut=2):
    """The projects module with what a reopening touches."""
    asked = []
    module = projects_host.build(answers={ReviewReopening: lambda command: asked.append(command) or reopened}, year=100)
    module.asked, module.recorded = asked, []
    module.record_staffing_reopenings = module.recorded.append
    module.staffing_shut_count = lambda: still_shut
    return module


def reopen(reopened, **keywords):
    game = Game(reopened, **keywords)
    result = game.reopen_restaffed_ventures(130)
    return game, result


def log_of(game):
    return [command for command in module_harness.sent(game) if isinstance(command, RecordEvent)]


game, result = reopen({"b", "a"})
check("the ventures module is asked to reopen what the staffing closed", game.asked == [ReviewReopening()])
check("the plants the review reopened are returned and counted", result == {"a", "b"} and game.recorded == [2], (result, game.recorded))
lines = log_of(game)
check("the household's log has one concerns_reopened line for the year", [(line.year, line.kind) for line in lines] == [(130, "concerns_reopened")], lines)
check("the line's facts are the plants reopened, in order, and the count still shut",
      lines[0].facts == {"reopened": ["a", "b"], "still_shut": 2}, lines[0].facts)
game, _ = reopen({"only"}, still_shut=0)
check("a single plant is a list of one with none still shut", log_of(game)[0].facts == {"reopened": ["only"], "still_shut": 0})
game, _ = reopen({"p5", "p3", "p1", "p4", "p2"})
check("every plant reopened is in the facts and all are counted",
      log_of(game)[0].facts["reopened"] == ["p1", "p2", "p3", "p4", "p5"] and game.recorded == [5])
game, result = reopen(set())
check("when nothing reopens nothing is recorded or said", result == set() and game.recorded == [] and log_of(game) == [])
