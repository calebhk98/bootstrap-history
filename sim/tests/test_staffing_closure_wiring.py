"""The yearly staffing closure and what a reopening costs. `concerns_to_close_for_staffing` hands the running concerns' draws, their
net values and the keep-staffed flags to `closures_for_shortfall` (replaced by a recorder; which concerns it picks is
test_staffing_choice_rules); `close_unstaffed_ventures` closes what the business's review shuts for staff and logs it with the
shortfall and what stopped earning; `opening_fee` is `reopen_fee` at the size reopened, the charge `restore_work` pays too; a plant
reopened keeps its first opening year, so the revenue ramp does not restart. Each runs on a stand-in carrying only what it reads."""

QUICK_TOPIC = True
UNDER_TEST = {"open_plant"}   # the method this module tests

from types import SimpleNamespace
from unittest import mock

from .harness import check

from sim.agents.business import Business
from sim.agents.business_plant import MOTHBALLED, Plant
from sim.agents.api import business_review
from sim.projects import staffing_shortfall
from sim.projects.state import ProjectsSeat
from sim.projects import constants as project_constants
from sim.reporting.api import RecordEvent
from sim.tests import module_harness, projects_host, ventures_host

NODES = {"mill": {"rev": 900.0, "up": 300.0}, "forge": {"rev": 500.0, "up": 450.0}}


def Shortfall(keep_staffed=()):
    """The projects module with what choosing closures reads."""
    module = projects_host.build(tree=NODES, seat=ProjectsSeat(keep_staffed=set(keep_staffed)))
    module._staffing_draws = lambda: {"mill": {"craftsmen": 3.0}, "forge": {"craftsmen": 2.0}}
    module._staffing_shortfalls = lambda totals: {}
    return module


game = Shortfall(keep_staffed={"forge"})
with mock.patch.object(staffing_shortfall, "closures_for_shortfall", return_value=["forge"]) as rule:
    picked = game.concerns_to_close_for_staffing()
draws, net_value, flagged, shortfalls_of = rule.call_args.args
check("the closures are the rule's pick", picked == ["forge"])
check("the rule is given the running concerns' draws and their revenue less running cost",
      draws == {"mill": {"craftsmen": 3.0}, "forge": {"craftsmen": 2.0}} and net_value == {"mill": 600.0, "forge": 50.0}, (draws, net_value))
check("the concerns flagged to stay staffed and the game's own shortfall reading are handed in",
      flagged == {"forge"} and shortfalls_of == game._staffing_shortfalls, (flagged, shortfalls_of))


def Closer(planned, closures):
    """The projects module with what the yearly closure touches."""
    module = projects_host.build(concern_rows_stopped=lambda node_ids: 123.46 * len(node_ids))
    module.STAFFING_REMEDIES = "remedies"
    module.recorded, module.review_asked = [], []
    module.concerns_to_close_for_staffing = lambda: planned
    module.staffing_held_totals = lambda: {"craftsmen": 9.0}
    module._staffing_shortfalls = lambda totals: {"craftsmen": 2.0}

    def review_ventures(rules, year):
        module.review_asked.append((rules, year))
        return [SimpleNamespace(entry_key=key) for key in closures]
    module.review_ventures = review_ventures
    module.record_staffing_closures = lambda count, shortfalls: module.recorded.append((count, shortfalls))
    module.staffing_shortfall_words = lambda shortfalls: "words"
    module.staffing_shut_count = lambda: 4
    return module


def logged(module):
    return [command for command in module_harness.sent(module) if isinstance(command, RecordEvent)]


closer = Closer(["mill", "forge"], ["forge", "mill"])
closed = closer.close_unstaffed_ventures(120)
check("the yearly review is run for the staffing rule alone, in the given year",
      closer.review_asked == [((business_review.STAFF_SHORT,), 120)], closer.review_asked)
check("what the review shuts is returned, counted, and set against the shortfall",
      closed == ["forge", "mill"] and closer.recorded == [(2, {"craftsmen": 2.0})], (closed, closer.recorded))
event, = logged(closer)
check("the log line is the closure event with the concerns, the shortfall and the earnings stopped",
      event.year == 120 and event.kind == "concerns_closed_unstaffed" and event.facts["concerns"] == ["forge", "mill"]
      and event.facts["short"] == {"craftsmen": 2.0} and event.facts["stops_earnings_per_year"] == 246.9, event.facts)
quiet = Closer([], [])
check("when the review shuts nothing nothing is recorded or logged", quiet.close_unstaffed_ventures(120) == [] and quiet.recorded == []
      and logged(quiet) == [])


FLOOR = project_constants.STARTER_FOUNDING_MIN_UNITS


def Opener():
    """The ventures module with the size a reopening restores and the fee at a size fixed."""
    module = ventures_host.build(capability_sets=(frozenset(), frozenset({"school"}), {}))
    module.reopen_units = lambda node_id: 0.8
    module.reopen_fee = lambda node_id, unit_count=1.0: 1000.0 * unit_count
    return module


check("opening a concern charges the reopening fee at the size it reopens at",
      Opener().opening_fee("mill") == (800.0, 0.8))
check("a starter founding of a scalable institution is charged at the size asked, never under the floor",
      Opener().opening_fee("school", 0.5) == (500.0, 0.5) and Opener().opening_fee("school", FLOOR / 2) == (1000.0 * FLOOR, FLOOR))
check("units asked of what is not scalable are ignored", Opener().opening_fee("mill", 3) == (800.0, 0.8))

business = Business(plants=[Plant(entry_key="mill", opened_year=100, state=MOTHBALLED, since_year=105, reason="staff_short")])
business.open_plant("mill", 115)
check("a plant reopened after a closure keeps its first opening year and its size, so the ramp does not restart",
      business.opened_year_of("mill", None) == 100 and business.state_of("mill") == "operating" and business.size_of("mill") == 1.0)
running = Business(plants=[Plant(entry_key="mill", opened_year=100)])
running.open_plant("mill", 120)
check("a plant already running that is opened again is restarted from that year", running.opened_year_of("mill", None) == 120)
