"""Active projects (the `active` dict, not a running concern): pacing, stalls, abandonment, stopping and restarting, the warning when
selling hours would starve a project, and the hour pace the material brake is applied to.

Regrouped from test_round8_fixes.py, test_round9.py, test_round10.py and test_round12_naive15.py. Each rule runs on the projects module, a stub game
or inputs the test builds: what a project is waiting on (`_waiting_on`), why a trade is short (`trade_shortage_kind`), the stall
gate's countdown and its abandonment, `stop_project`'s kept money and the credit on a restart, `why`'s cost block, the sale-of-hours
warning, and `project_hour_pace`. The crawl of a project short of a trade is test_project_crawl_rules; a start refused for the gross price of a nearly paid project is `cash_covers_start` below."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.projects.api import StopProject, funding
from sim.tests import projects_host
cash_covers_start, paid_credit = funding.cash_covers_start, funding.paid_credit
from sim.projects import progress_rules
from sim.projects.start_rules import STALL_YEARS_BEFORE_ABANDONMENT
from sim.reporting.api import RecordEvent
from sim.labour.hours_sale_warning import starved_projects, starving_warning
from sim.refusal import cause_of, facts_of
from sim.ui.proto.state_waiting import _waiting_on
from sim.ui.proto.techtree import _explain_cost
from sim.tests import module_harness
from sim.tests.ui_stand_in import FactViews, Game as LabourStub

NODE = {"name": "Slow work", "yrs": 10, "ph": 500, "lab": {}, "cat": "x"}


def a_game(supply=None, demand=None, spending=1.0e9, cost=10000.0, throttle=(1.0, None), standing=None, **fields):
    """A stub game for `_waiting_on`: hours each trade can field, the portfolio's demand on them, what the household can raise."""
    supply, demand = dict(supply or {}), dict(demand or {})

    class Game(FactViews):
        civ = {}

        def trade_shortage_kind(self, trade_id, need, total_demand=None):
            return progress_rules.shortage_kind(self.labour.hours_you_can_call_on(trade_id), need, total_demand)

    game = Game()
    game.trade_demand_vs_supply = lambda: {trade: {"demand_hours_this_year": hours} for trade, hours in demand.items()}
    game.labour = LabourStub(hours_you_can_call_on=lambda trade: supply.get(trade, 1.0e9), director_pool=lambda: 2000.0,
                                  director_hours_committed=lambda: 500.0)
    game.project_cost = lambda node_id: cost
    game.spending_power = lambda purpose: spending
    game.peek_project_resource_throttle = lambda node_id: throttle
    game.hour_standing = lambda node_id: standing
    for name, value in fields.items():
        setattr(game, name, value)
    return game


def waiting(game, node, **progress):
    entry = dict(ph_left=0.0, yrs=1.0, spent=0.0, cost_left=1000.0)
    entry.update(progress)
    return _waiting_on(game, {"p": node}, "p", entry, entry["cost_left"])


# --- money: the pace is not a shortage of money
check("a rich player is told the pace, not that they are short of money",
      cause_of(waiting(a_game(), NODE)) == "money_pace", waiting(a_game(), NODE))
check("...and a player who cannot raise the instalment at all is told that",
      cause_of(waiting(a_game(spending=0.0), NODE)) == "money_blocked", waiting(a_game(spending=0.0), NODE))
check("...and one who can raise something, but not the instalment, is told it is unfunded",
      cause_of(waiting(a_game(spending=50.0), NODE)) == "money_unfunded", waiting(a_game(spending=50.0), NODE))

# --- hours spent and nothing owed: the calendar, not a stale 'your hours'
calendar = waiting(a_game(), NODE, ph_left=0.0, yrs=0.5, spent=100.0, cost_left=0.0)
check("a project with 100% of its hours spent and 0 still owed reports waiting on the calendar, not a stale 'your hours'",
      cause_of(calendar) == "calendar" and calendar.startswith("the calendar"), calendar)  # presentation: the sentence leads with the calendar

# --- the founder's hours
sharing = waiting(a_game(standing=(2, 3, 1500.0)), NODE, ph_left=100.0)
check("hours owed and shared with other projects name the project's priority",
      cause_of(sharing) == "founder_hours" and "#2 of 3" in sharing, sharing)  # presentation: the rank is named
alone = waiting(a_game(), NODE, ph_left=100.0)
check("hours owed on the only project in hand say how many hours are still to do", cause_of(alone) == "founder_hours", alone)
braked = waiting(a_game(throttle=(0.5, "iron")), NODE, ph_left=100.0)
check("a project running well under its pace for want of a material says which", cause_of(braked) == "materials" and "iron" in braked, braked)
check("a negligible material shortage is not blamed", cause_of(waiting(a_game(throttle=(0.99, "iron")), NODE, ph_left=100.0)) != "materials")

# --- staffing: a trade the society cannot field, one only the player's own work has booked, both at once
STAFFED = dict(NODE, lab={"engineer": 500.0})
none_here = waiting(a_game(supply={"engineer": 0.0}), STAFFED, ph_left=100.0)
check("a project needing a trade nobody here has says nobody is there to do the work",
      cause_of(none_here) == "staffing" and none_here.startswith("nobody to do the work") and "engineer" in none_here, none_here)
booked = waiting(a_game(supply={"engineer": 1000.0}, demand={"engineer": 1.0e9}), STAFFED, ph_left=100.0)
check("a trade the society can field but the player's other work has booked is a booking, not a shortage",
      cause_of(booked) == "trade_hours" and booked.startswith("trade hours already booked"), booked)
plenty = waiting(a_game(supply={"engineer": 1000.0}, demand={"engineer": 10.0}), STAFFED, ph_left=100.0)
check("a trade with hours to spare is not blamed", cause_of(plenty) not in ("staffing", "trade_hours"), plenty)
TWO = dict(NODE, lab={"engineer": 500.0, "scribe": 500.0})
both = waiting(a_game(supply={"engineer": 0.0, "scribe": 1000.0}, demand={"scribe": 1.0e9}), TWO, ph_left=100.0)
check("a project short on two different trades at once names both, not just the first one found",
      "engineer" in both and "scribe" in both, both)
check("...and still leads with 'nobody to do the work', so 'portfolio' classifies this the same way it always has",
      both.startswith("nobody to do the work") and cause_of(both) == "staffing", both)  # presentation: the sentence leads with the shortage
drawn = waiting(a_game(supply={"engineer": 0.0}), STAFFED, ph_left=100.0, lab_left={"engineer": 0.0})
check("a project that has already drawn everything it needed from a trade is not blamed for that trade vanishing",
      cause_of(drawn) not in ("staffing", "trade_hours"), drawn)
still_owed = waiting(a_game(supply={"engineer": 0.0}), STAFFED, ph_left=100.0, lab_left={"engineer": 200.0})
check("...while a project that still owes a trade something is told so",
      cause_of(still_owed) == "staffing" and "engineer" in still_owed, still_owed)

# --- why a trade is short
def kind_of(supply, need, demand):
    return progress_rules.shortage_kind(supply, need, demand)


check("a trade the society cannot field in the hours wanted is a staffing shortage", kind_of(100.0, 500.0, 10.0) == "staffing")
check("a trade it can field, with the portfolio asking for more, is booked", kind_of(1000.0, 500.0, 5000.0) == "booked")
check("a trade with hours to spare against the whole portfolio is no shortage", kind_of(1000.0, 500.0, 800.0) is None)
check("a caller that already knows the project fell short gets booked when the society can field the hours",
      kind_of(1000.0, 500.0, None) == "booked")

# --- the stall gate: a countdown, said every year, before the money goes
def gated(blocked_trades=("engineer",), lab_left=None, stalled_years=0):
    progress = {"stalled_years": stalled_years, "hours_offered_this_year": 9.0, "hours_effective_this_year": 9.0}
    if lab_left is not None:
        progress["lab_left"] = lab_left
    projects = LabourStub(active={"p": progress}, bountied=set())
    host = projects_host.build(market_supply=lambda trade: 0.0 if trade in blocked_trades else 1000.0, legacy_projects=projects, year=100)
    stopped = host._project_progress_trade_gate("p", progress, {"lab": {"engineer": 500.0, "smith": 100.0}})
    log = [(100, command) for command in module_harness.sent(host) if isinstance(command, RecordEvent)]
    return stopped, progress, log, host


stopped, progress, log, _host = gated()
check("a project needing more of a trade than exists stalls, and says so the first year, not the fourth",
      stopped and progress["stalled_years"] == 1 and len(log) == 1 and log[0][1].kind == "project_cannot_go_on"
      and log[0][1].facts["project"] == "p" and log[0][1].facts["trades"] == ["engineer"], log)
check("...and the entry carries the countdown and the trade that would save it",
      progress["blocked_on_trades"] == ["engineer"] and log[0][1].facts["years_left"] == STALL_YEARS_BEFORE_ABANDONMENT - 1, progress)
check("...and the year's hours it was offered are zeroed, not left looking as if they applied",
      progress["hours_offered_this_year"] == 0.0 and progress["hours_effective_this_year"] == 0.0, progress)
stopped, progress, log, _host = gated(lab_left={"engineer": 0.0, "smith": 50.0})
check("a project that has already drawn everything it needed from a trade is not killed when that trade vanishes",
      not stopped and progress["stalled_years"] == 0 and not log, (progress, log))
stopped, progress, log, _host = gated(lab_left={"engineer": 200.0, "smith": 50.0})
check("...while one that still owes the trade something is caught the first year it has nobody to do that work",
      stopped and any(line.kind == "project_cannot_go_on" and "engineer" in line.facts["trades"] for _year, line in log), log)
stopped, progress, log, host = gated(stalled_years=STALL_YEARS_BEFORE_ABANDONMENT - 1)
check("after the countdown the project is abandoned and the log says what was lost",
      stopped and "p" not in host.needs.legacy_projects().active and log[0][1].kind == "project_halted_no_labour", log)
stopped, progress, log, _host = gated(blocked_trades=(), stalled_years=2)
check("a project with its trades again has its countdown cleared", not stopped and progress["stalled_years"] == 0)

# --- stopping keeps the money that was paid; beginning again bills only the remainder
def stopped_game(spent):
    state = projects_host.projects_state(active={"p": {"spent": spent, "ph_left": 100.0}}, paid_towards=None)
    module = projects_host.build(legacy_projects=state)
    return state, module, module.stop_project(StopProject("p"))
state, _module, (ok, message) = stopped_game(300.0)
check("stopping a project keeps the money already paid", ok and state.paid_towards == {"p": 300.0}, state.paid_towards)
state, _module, (ok, message) = stopped_game(0.2)
check("a project that had paid next to nothing keeps nothing", ok and not state.paid_towards, state.paid_towards)
state, module, (ok, message) = stopped_game(1.0)
check("stopping something that is not active is refused", module.stop_project(StopProject("q")) == (False, "not active"))
check("money already paid comes off the bill, never more than the price",
      paid_credit(1000.0, 300.0) == 300.0 and paid_credit(1000.0, 5000.0) == 1000.0 and paid_credit(1000.0, None) == 0.0
      and paid_credit(1000.0, -5.0) == 0.0)
check("a nearly paid project is not refused for its gross price",
      cash_covers_start(1000.0, 995.0, 0.0, 10.0) and not cash_covers_start(1000.0, 0.0, 0.0, 10.0))

# --- `why` shows what `start` would charge once money is sunk into the node
def explained(paid, done=(), active=()):
    game = LabourStub(
        project_material_bill=lambda node_id: {"cost_of_missing": 0.0, "rows": []}, civ_cost_factor=lambda node_id: 1.0,
        geography=LabourStub(material_cost_factor=lambda node_id: 1.0), opposition_factor=lambda node_id: 1.0,
        rebuild_work_factor=lambda node_id: 1.0,
        cost_money_factor=lambda: 1.0, money_real=1.0, project_cost=lambda node_id: 1000.0, year=100,
        paid_towards={"p": paid} if paid else {}, done=set(done), active=set(active))
    return _explain_cost(game, {"p": NODE}, "p", dict(NODE, _labour_cost=800.0, cap=200.0))
sunk = explained(400.0)
check("`why` on a halted, partly-paid project shows both the gross total and what 'start' would actually charge",
      sunk["already_paid_towards_this"] == 400.0 and sunk["what_start_would_actually_charge"] == 600.0 and sunk["total"] == 1000.0, sunk)
check("...while a project with nothing sunk into it gets no discount field at all", "already_paid_towards_this" not in explained(0.0))
check("...nor one that is already done", "already_paid_towards_this" not in explained(400.0, done=("p",)))
check("...nor one that is already running", "already_paid_towards_this" not in explained(400.0, active=("p",)))

# --- selling every founder-hour is allowed, with a warning naming what it starves
check("a sale that leaves the projects the hours they want warns of nothing", starving_warning({"small": 40.0}, 1990.0) is None)
check("no project in hand warns of nothing", starving_warning({}, 0.0) is None)
big = starving_warning({"big_work": 500.0}, 0.0)
check("a sale that leaves a project short names it and the hours it still wants",
      big is not None and "big_work" in big and "hours" in big, big)  # presentation: the warning names the project and the hours
check("...naming the two hungriest, and counting the rest",
      starved_projects({"a": 100.0, "b": 300.0, "c": 200.0, "d": 50.0}, 10.0) == [("b", 300.0), ("c", 200.0), ("a", 100.0), ("d", 50.0)]
      and ", and 2 more" in starving_warning({"a": 100.0, "b": 300.0, "c": 200.0, "d": 50.0}, 10.0))  # presentation: the count of the rest
check("a project wanting no more than is left is not starved", starved_projects({"a": 100.0}, 100.0) == [])

# --- the hour pace is what a project WANTS, with no material brake folded in
def pace(ph_left, throttle, bountied=()):
    host = projects_host.build(
        legacy_projects=LabourStub(active={"p": {"ph_left": ph_left}}, bountied=set(bountied)), tree={"p": dict(NODE, ph=500, yrs=2)},
        resource_throttle=lambda node_id: (throttle, None))
    return host.project_hour_pace("p")


check("project_hour_pace reports what a project WANTS, with no material brake folded in, because its callers apply the brake themselves "
      "and min(remaining, want) * throttle is not min(remaining, want * throttle)",
      abs(pace(300.0, 0.5) - pace(300.0, 1.0)) < 1e-9 and pace(300.0, 1.0) > 0, (pace(300.0, 0.5), pace(300.0, 1.0)))
check("the pace is the larger of the hours left and the node's yearly share of its hours", pace(300.0, 1.0) == 300.0 and pace(10.0, 1.0) == 250.0)
check("a bounty is worked by whoever claims the prize, so the poster's pace is nothing", pace(300.0, 1.0, bountied=("p",)) == 0.0)
