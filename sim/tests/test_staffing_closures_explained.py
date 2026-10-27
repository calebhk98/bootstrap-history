"""Staffing closures explained: Complaints 229, 215, 201, 202, 231, 242, 233, 205, 206, 235, 246. The rules are called on
stubs over the real mixins (the year's tally and summary, the unused-hours notes) and on the plain functions behind the
log lines and the sentences; the recommendation of `stuck` is test_stuck_shut_ventures_rule. The spare-number arithmetic (held, in use, allowance) is
test_staffing_warnings."""

QUICK_TOPIC = True

from sim.tests import workforce_stand_in
import re
from types import SimpleNamespace

from .harness import check

from sim.agents.api import business_review
from sim.engine.allocation_notes import AllocationNotesMixin
from sim.engine.data import TRADE_FAMILY
from sim.engine.projects_staffing import StaffingMixin
from sim.engine.projects_staffing_report import StaffingReportMixin
from sim.projects.staffing_events import unstaffed_closure_line
from sim.labour.hire_outcome import craft_trades_report
from sim.refusal import cause_of, facts_of
from sim.ui.proto.dispatch_ventures import _non_craft_labour_names, _scholar_family_names
from sim.tests import event_stand_in

STAFF = business_review.STAFF_SHORT


# ---- 233: the closure line says why, how many are still shut, and names the remedies ---------------------------------
class Report(StaffingReportMixin, StaffingMixin):
    """The tally and the summary over a stub of the projects' record."""

    def __init__(self, shut=(), year=100):
        self.state = SimpleNamespace(
            projects=SimpleNamespace(staffing_tally={}, closures={node_id: {"reason": STAFF, "year": year - 1} for node_id in shut},
                                     mothballed=set(shut)),
            scenario=SimpleNamespace(year=year))


line = unstaffed_closure_line(["mill"], {"craftsmen": 2.1}, Report.staffing_shortfall_words({"craftsmen": 2.1}), 1,
                              StaffingReportMixin.STAFFING_REMEDIES, 300.0)
for remedy in ("keep", "reserve", "auto_replace_foreman"):
    check("the closure line names '%s' as a remedy" % remedy, remedy in line, line)
check("the closure line names the resource that ran short and how short", "craftsmen (short 2.1 full-time)" in line, line)
check("the closure line counts those still shut and names what closed", "1 now shut" in line and "mill" in line, line)
check("the closure line keeps its facts: what closed, why, what was short and what it stopped earning",
      facts_of(line)["concerns"] == ["mill"] and facts_of(line)["closed_because"] == "short_staffed"
      and facts_of(line)["short"] == {"craftsmen": 2.1} and facts_of(line)["stops_earnings_per_year"] == 300.0
      and cause_of(line) == "concerns_closed_unstaffed", facts_of(line))
many = unstaffed_closure_line(["a", "b", "c", "d", "e", "f"], {}, "nothing", 6, "", 0.0)
check("six closures name four and say 'and others'", "and others" in many and "a, b, c, d" in many, many)

report = Report(shut=["mill"])
report.record_staffing_closures(1, {"craftsmen": 2.1})
summary = report.staffing_closure_summary()
check("the closure summary counts closed, reopened and still shut",
      re.search(r"closed 1\b", summary) and re.search(r"reopened 0\b", summary) and re.search(r"still shut 1\b", summary), summary)
check("...and names the cause and the remedies", "craftsmen (short 2.1 full-time)" in summary and "keep <id> staffed" in summary, summary)
report.state.projects.closures.clear()
report.state.projects.mothballed.clear()
report.record_staffing_reopenings(1)
check("the summary reflects the reopening and the shut count falls", re.search(r"reopened 1\b", report.staffing_closure_summary())
      and re.search(r"still shut 0\b", report.staffing_closure_summary()), report.staffing_closure_summary())
check("no summary when nothing has closed", Report().staffing_closure_summary() is None)
last_year = Report()
last_year.state.projects.staffing_tally = {"year": 99, "closed": 3, "reopened": 0, "short": {}}
check("a new year starts the tally afresh", last_year.staffing_closure_summary() is None, last_year.state.projects.staffing_tally)
by_choice = Report()
by_choice.state.projects.closures["m"] = {"reason": StaffingMixin.CLOSED_BY_CHOICE, "year": 90}
by_choice.state.projects.mothballed.add("m")
check("a concern shut by choice is not shut for want of staff", by_choice.staffing_shut_count() == 0 and by_choice.staffing_closure_summary() is None)


# ---- 205, 206: a standing order that keeps falling short is reported once until it changes -------------------------------
class Notes(AllocationNotesMixin):
    """The unused-hours report over a household that logs and keeps the standing orders."""
    send = event_stand_in.send

    def __init__(self, orders):
        self.log = []
        self.state = SimpleNamespace(
            household=SimpleNamespace(unused_hours_reported={}, hour_allocations=dict(orders), log=self.log),
            scenario=SimpleNamespace(year=100))
        self.view = workforce_stand_in.view_of(self.state.household)
        self.nodes = {"school": {"name": "School founding"}, "academy": {"name": "Academy"}}

    def said_about(self, name):
        return [message for _year, message in self.log if "DIRECTED HOURS UNUSED" in message and name in message]


pace = "its own pace this year - at most %d hours could use the rest"
notes = Notes({"school": 1000.0})
for year_number in range(3):
    before = len(notes.log)
    notes.report_unused_directed_hours([("school", 700.0, pace % (300 - year_number))])
    check("year %d: a shortfall that falls short the same way is reported once, not yearly" % year_number,
          len(notes.log) - before == (1 if year_number == 0 else 0), notes.log)
check("the report names the command that lowers the standing order to what the project can use, and says it will not repeat",
      "allocate school 300" in notes.log[0][1] and "allocate school 0" in notes.log[0][1] and "said once" in notes.log[0][1], notes.log[0][1])
notes.state.household.hour_allocations["school"] = 600.0
before = len(notes.log)
notes.report_unused_directed_hours([("school", 300.0, pace % 300)])
check("a changed standing order is reported afresh", len(notes.log) - before == 1, notes.log)
notes.report_unused_directed_hours([])
before = len(notes.log)
notes.report_unused_directed_hours([("school", 300.0, pace % 300)])
check("a shortfall that recovered and returned is reported afresh", len(notes.log) - before == 1, notes.log)
before = len(notes.log)
notes.report_unused_directed_hours([("school", 300.0, "a different reason")])
check("the same order falling short for a different reason is reported afresh", len(notes.log) - before == 1, notes.log)
check("the report carries its facts: the project and the hours unused", facts_of(notes.log[0][1])["project"] == "school"
      and facts_of(notes.log[0][1])["hours_unused"] == 700.0, facts_of(notes.log[0][1]))
other = Notes({"school": 1000.0, "academy": 500.0})
other.report_unused_directed_hours([("school", 100.0, "reason one"), ("academy", 100.0, "reason one")])
check("each project's order is reported on its own", len(other.said_about("School")) == 1 and len(other.said_about("Academy")) == 1)

# ---- 246: the interchangeability sentence comes from the trade table ---------------------------------------------------------
scholar_trades = sorted(trade for trade, family in TRADE_FAMILY.items() if family == "scholar")
craft_trades = sorted(trade for trade, family in TRADE_FAMILY.items() if family == "craft")
sentence = _scholar_family_names()
check("every scholar-family trade is named in the sentence", bool(scholar_trades) and all(trade + "s" in sentence for trade in scholar_trades), sentence)
check("no craft trade is called a scholar in the sentence", bool(craft_trades) and not any(trade + "s" in sentence for trade in craft_trades), sentence)
labour = SimpleNamespace(craft_trades_report=lambda: craft_trades_report(["smith", "chemist", "potter", "labourer"], lambda trade: trade in ("smith", "potter")))
check("the labouring trades named are those the supervision check says are not craft, and not the scholar family's",
      _non_craft_labour_names(SimpleNamespace(labour=labour)) == ("labourers" if TRADE_FAMILY.get("chemist") == "scholar" else "chemists, labourers"),
      _non_craft_labour_names(SimpleNamespace(labour=labour)))
check("the craft test splits the trades", craft_trades_report(["b", "a", "c"], lambda trade: trade == "a") == {"craft": ["a"], "not_craft": ["b", "c"]})
