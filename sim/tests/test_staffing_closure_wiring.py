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
from sim.engine import projects_staffing, projects_staffing_shortfall
from sim.engine.projects_staffing import StaffingMixin
from sim.engine.projects_staffing_shortfall import StaffingShortfallMixin
from sim.engine.projects_ventures import VenturesMixin
from sim.refusal import cause_of, facts_of

NODES = {"mill": {"rev": 900.0, "up": 300.0}, "forge": {"rev": 500.0, "up": 450.0}}


class Shortfall(StaffingShortfallMixin):
    """The parts of a Sim that choosing closures reads."""
    nodes = NODES

    def __init__(self, keep_staffed=()):
        self.state = SimpleNamespace(projects=SimpleNamespace(keep_staffed=set(keep_staffed)))

    def _staffing_draws(self):
        return {"mill": {"craftsmen": 3.0}, "forge": {"craftsmen": 2.0}}

    def _staffing_shortfalls(self, totals):
        return {}


game = Shortfall(keep_staffed={"forge"})
with mock.patch.object(projects_staffing_shortfall, "closures_for_shortfall", return_value=["forge"]) as rule:
    picked = game.concerns_to_close_for_staffing()
draws, net_value, flagged, shortfalls_of = rule.call_args.args
check("the closures are the rule's pick", picked == ["forge"])
check("the rule is given the running concerns' draws and their revenue less running cost",
      draws == {"mill": {"craftsmen": 3.0}, "forge": {"craftsmen": 2.0}} and net_value == {"mill": 600.0, "forge": 50.0}, (draws, net_value))
check("the concerns flagged to stay staffed and the game's own shortfall reading are handed in",
      flagged == {"forge"} and shortfalls_of == game._staffing_shortfalls, (flagged, shortfalls_of))


class Closer(StaffingMixin):
    """The parts of a Sim that the yearly closure touches."""
    STAFFING_REMEDIES = "remedies"

    def __init__(self, planned, closures):
        self.state = SimpleNamespace(household=SimpleNamespace(log=[]))
        self.planned, self.closures = planned, closures
        self.recorded = []
        self.review_asked = []
        self.labour = SimpleNamespace(yearly_value_of=lambda node_ids: 123.46 * len(node_ids))

    def concerns_to_close_for_staffing(self):
        return self.planned

    def staffing_held_totals(self):
        return {"craftsmen": 9.0}

    def _staffing_shortfalls(self, totals):
        return {"craftsmen": 2.0}

    def review_ventures(self, rules, year):
        self.review_asked.append((rules, year))
        return [SimpleNamespace(entry_key=key) for key in self.closures]

    def record_staffing_closures(self, count, shortfalls):
        self.recorded.append((count, shortfalls))

    def staffing_shortfall_words(self, shortfalls):
        return "words"

    def staffing_shut_count(self):
        return 4


closer = Closer(["mill", "forge"], ["forge", "mill"])
closed = closer.close_unstaffed_ventures(120)
check("the yearly review is run for the staffing rule alone, in the given year",
      closer.review_asked == [((projects_staffing.business_review.STAFF_SHORT,), 120)], closer.review_asked)
check("what the review shuts is returned, counted, and set against the shortfall",
      closed == ["forge", "mill"] and closer.recorded == [(2, {"craftsmen": 2.0})], (closed, closer.recorded))
(year, line), = closer.state.household.log
check("the log line is the closure event with the concerns, the shortfall and the earnings stopped",
      year == 120 and cause_of(line) == "concerns_closed_unstaffed" and facts_of(line)["concerns"] == ["forge", "mill"]
      and facts_of(line)["short"] == {"craftsmen": 2.0} and facts_of(line)["stops_earnings_per_year"] == 246.9, facts_of(line))
quiet = Closer([], [])
check("when the review shuts nothing nothing is recorded or logged", quiet.close_unstaffed_ventures(120) == [] and quiet.recorded == []
      and quiet.state.household.log == [])


class Opener(VenturesMixin):
    """The parts of a Sim that the charge for opening reads."""
    SCALABLE_INSTITUTIONS = {"school"}
    STARTER_FOUNDING_MIN_UNITS = 0.25

    def reopen_units(self, node_id):
        return 0.8

    def reopen_fee(self, node_id, unit_count=1.0):
        return 1000.0 * unit_count


check("opening a concern charges the reopening fee at the size it reopens at",
      Opener().opening_fee("mill") == (800.0, 0.8))
check("a starter founding of a scalable institution is charged at the size asked, never under the floor",
      Opener().opening_fee("school", 0.5) == (500.0, 0.5) and Opener().opening_fee("school", 0.1) == (250.0, 0.25))
check("units asked of what is not scalable are ignored", Opener().opening_fee("mill", 3) == (800.0, 0.8))

business = Business(plants=[Plant(entry_key="mill", opened_year=100, state=MOTHBALLED, since_year=105, reason="staff_short")])
business.open_plant("mill", 115)
check("a plant reopened after a closure keeps its first opening year and its size, so the ramp does not restart",
      business.opened_year_of("mill", None) == 100 and business.state_of("mill") == "operating" and business.size_of("mill") == 1.0)
running = Business(plants=[Plant(entry_key="mill", opened_year=100)])
running.open_plant("mill", 120)
check("a plant already running that is opened again is restarted from that year", running.opened_year_of("mill", None) == 120)
