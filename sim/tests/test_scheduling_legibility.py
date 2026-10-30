"""Project scheduling made legible: what a project is waiting on (five precise reasons), the portfolio's demand against
each trade's supply, the note when a start would oversubscribe a trade, and the warning before a multi-year step wastes
hours. Each rule runs on tables or a stand-in game the test builds (no game): the real `_waiting_on` and the projects module's
shortage rule over a stand-in of trades, money and queue. The allocator's stored shares are
test_step_progress_pool_standing."""
from types import SimpleNamespace

from .harness import check

from sim.projects import progress_rules
from sim.projects.trade_demand import oversubscription_notes, trade_demand_table
from sim.refusal import cause_of
from sim.ui.proto.economy import _portfolio_constraint as _PCON
from sim.ui.proto.multi_year_warning import multi_year_hours_warning
from sim.ui.proto.state_waiting import _waiting_on
from sim.tests.ui_stand_in import Game
from sim.tests.ui_stand_in import FactViews

QUICK_TOPIC = True


# --- 2a. per-trade demand against supply, aggregated, before committing
SUPPLY = {"chemist": 1500.0, "smith": 5000.0}
WANTS = {"a": {"chemist": 400.0, "smith": 100.0}, "b": {"chemist": 700.0}, "c": {"chemist": 500.0}, "d": {}}
table = trade_demand_table(WANTS, SUPPLY.get)
check("the demand of a trade is the sum of each project's own desired hours of it",
      table["chemist"]["demand_hours_this_year"] == 1600.0 and table["smith"]["demand_hours_this_year"] == 100.0, table)
check("...against what the trade can supply, flagged oversubscribed only when demand exceeds supply",
      table["chemist"]["supply_hours_this_year"] == 1500.0 and table["chemist"]["oversubscribed"] is True
      and table["smith"]["oversubscribed"] is False, table)
check("...and names every project actually drawing on it, in order, and a project that wants nothing is in no row",
      table["chemist"]["projects_drawing_on_it"] == ["a", "b", "c"] and table["smith"]["projects_drawing_on_it"] == ["a"]
      and set(table) == {"chemist", "smith"}, table)
exact = trade_demand_table({"a": {"chemist": 1500.0}}, SUPPLY.get)
check("demand exactly equal to supply is not oversubscribed", exact["chemist"]["oversubscribed"] is False)
check("the table does not depend on the order the projects are given in",
      trade_demand_table(dict(reversed(list(WANTS.items()))), SUPPLY.get) == table)
check("no active project means an empty table", trade_demand_table({}, SUPPLY.get) == {})

# --- 2b. the same oversubscription, said at `start`
numbers = lambda amount: "%d" % round(amount)
demand_now = {"chemist": {"demand_hours_this_year": 80.0, "projects_drawing_on_it": ["first"]}}
notes = oversubscription_notes(demand_now, {"chemist": {"desired": 100.0}}, {"chemist": 150.0}.get, set(), numbers)
check("a start that alone fits (100 of 150) but not alongside the first (80 + 100) names the trade, the new total "
      "and what the trade supplies",
      len(notes) == 1 and notes[0].startswith("chemist:") and "180" in notes[0] and "150" in notes[0]
      and "1 other active project already" in notes[0], notes)
check("a start that fits alongside the others says nothing",
      oversubscription_notes(demand_now, {"chemist": {"desired": 70.0}}, {"chemist": 150.0}.get, set(), numbers) == [])
check("a trade already reported as impossible is not reported again, nor one nobody supplies",
      oversubscription_notes(demand_now, {"chemist": {"desired": 100.0}}, {"chemist": 150.0}.get, {"chemist"}, numbers) == []
      and oversubscription_notes({}, {"chemist": {"desired": 100.0}}, {"chemist": 0.0}.get, set(), numbers) == [])
# presentation: the note counts the competing projects
check("with no other project drawing on the trade the note counts none",
      "0 other active projects already" in oversubscription_notes({}, {"smith": {"desired": 200.0}}, {"smith": 100.0}.get, set(), numbers)[0])


# --- 3. five precise reasons, not a blurred "nobody to do the work"
class _Stub(FactViews):
    """A game as `_waiting_on` reads it: a trade's supply, the portfolio's demand, money, the throttle and the queue."""

    def __init__(self, supply=None, demand=None, spending=1.0e9, cost=1000.0, throttle=(1.0, None), standing=None,
                 director_pool=2000.0, committed=0.0):
        self.civ = {"id": "stub"}
        self._demand = demand or {}
        self._spending, self._cost, self._throttle, self._standing = spending, cost, throttle, standing
        self.labour = Game(hours_you_can_call_on=lambda trade: (supply or {}).get(trade, 0.0),
                                      director_pool=lambda: director_pool, director_hours_committed=lambda: committed)

    def trade_demand_vs_supply(self):
        return self._demand

    def project_cost(self, node_id):
        return self._cost

    def spending_power(self, kind):
        return self._spending

    def peek_project_resource_throttle(self, node_id):
        return self._throttle

    def hour_standing(self, node_id):
        return self._standing

    def trade_shortage_kind(self, trade_id, need, total_demand=None):
        return progress_rules.shortage_kind(self.labour.hours_you_can_call_on(trade_id), need, total_demand)


NODE = {"yrs": 2, "ph": 100, "lab": {"chemist": 1000.0}}
NODES = {"work": NODE}


def _progress(**fields):
    return dict({"ph_left": 50.0, "yrs": 0.0, "lab_left": {"chemist": 1000.0}}, **fields)


none_at_all = _waiting_on(_Stub(supply={"chemist": 0.0}), NODES, "work", _progress(), 800.0)
check("an ABSOLUTE staffing shortage (this society can field none of the trade at all) is its own precise reason",
      cause_of(none_at_all) == "staffing" and _PCON(none_at_all) == "staffing", none_at_all)
booked = _waiting_on(_Stub(supply={"chemist": 600.0}, demand={"chemist": {"demand_hours_this_year": 900.0}}),
                     NODES, "work", _progress(), 800.0)
check("a trade the society CAN field but your OWN other active work has booked is a different, distinct reason "
      "with a different remedy",
      cause_of(booked) == "trade_hours" and _PCON(booked) == "trade_hours" and cause_of(booked) != cause_of(none_at_all), booked)
both = _waiting_on(_Stub(supply={"chemist": 0.0, "smith": 600.0}, demand={"smith": {"demand_hours_this_year": 900.0}}),
                   {"work": {"yrs": 2, "ph": 100, "lab": {"chemist": 1000.0, "smith": 1000.0}}}, "work",
                   _progress(lab_left={"chemist": 1000.0, "smith": 1000.0}), 800.0)
# presentation: both shortages are named in one sentence, the absolute one first
check("a project short one trade absolutely and another only to its own other work reports both, the absolute one first",
      cause_of(both) == "staffing" and "chemist" in both and "smith" in both and both.index("chemist") < both.index("smith"), both)
free = _Stub(supply={"chemist": 5000.0}, demand={"chemist": {"demand_hours_this_year": 500.0}})
check("a trade with enough supply and demand within it blocks nothing: the next reason is read",
      cause_of(_waiting_on(free, NODES, "work", _progress(), 800.0)) == "founder_hours")
materials = _waiting_on(_Stub(supply={"chemist": 5000.0}, throttle=(0.5, "saltpetre")), NODES, "work", _progress(), 800.0)
check("a project short of nothing else can still be waiting on MATERIALS: one economy-wide shortage scales its hours, "
      "a fifth distinct reason that names the input and the pace",
      cause_of(materials) == "materials" and _PCON(materials) == "materials" and "saltpetre" in materials and "50%" in materials,
      materials)
check("a throttle under two percent is noise and is not reported",
      cause_of(_waiting_on(_Stub(supply={"chemist": 5000.0}, throttle=(0.99, "saltpetre")), NODES, "work", _progress(), 800.0))
      == "founder_hours")
money_done = _progress(ph_left=0.0)
paced = _waiting_on(_Stub(supply={"chemist": 5000.0}, cost=1000.0), NODES, "work", money_done, 800.0)
check("with the work done and the money in hand to cover a year's instalment, the wait is the pace money can be absorbed at",
      cause_of(paced) == "money_pace" and _PCON(paced) == "money", paced)
check("with no money at all it is fully blocked, and with some but not a year's instalment it is unfunded",
      cause_of(_waiting_on(_Stub(supply={"chemist": 5000.0}, spending=0.0), NODES, "work", money_done, 800.0)) == "money_blocked"
      and cause_of(_waiting_on(_Stub(supply={"chemist": 5000.0}, spending=100.0), NODES, "work", money_done, 800.0)) == "money_unfunded")
calendar = _waiting_on(_Stub(supply={"chemist": 5000.0}), NODES, "work", money_done, 0.0)
check("with the work and the money done, the wait is the calendar", cause_of(calendar) == "calendar" and _PCON(calendar) == "calendar", calendar)
queued = _waiting_on(_Stub(supply={"chemist": 5000.0}, standing=(2, 3, 2000.0)), NODES, "work", _progress(), 800.0)
# presentation: the wait names the rank and the pool
check("hours the project shares with others name its rank, how many share and the pool, still the founder-hours bucket",
      cause_of(queued) == "founder_hours" and _PCON(queued) == "founder_hours" and "priority #2 of 3" in queued and "2,000" in queued, queued)

# the classifier also reads plain wording (a saved or foreign sentence), and a reply that is not text is unclear
check("calendar and money are classified from their wording as well",
      _PCON("the calendar") == "calendar"
      and _PCON("money: 40 still owed and this year's instalment of 10 is more than you can raise") == "money")
check("'your hours', enriched with the allocator's rank and pool, still classifies as the founder-hours bucket",
      _PCON("your hours") == "founder_hours"
      and _PCON("your hours: priority #1 of 2 active projects sharing this year's 2,000 directed hours; more") == "founder_hours")
check("text of no known kind, or no text, is unclear", _PCON("something else") == "unclear" and _PCON(None) == "unclear")

# --- the shortage kind itself
shortage = _Stub(supply={"chemist": 100.0})
check("a trade that cannot supply the need at all is a staffing shortage, whatever the demand",
      shortage.trade_shortage_kind("chemist", 150.0, 10.0) == "staffing")
check("a trade that can supply the need but is overdrawn by the portfolio is booked",
      shortage.trade_shortage_kind("chemist", 50.0, 300.0) == "booked")
check("a trade that can supply the need and the demand is no shortage",
      shortage.trade_shortage_kind("chemist", 50.0, 100.0) is None)
check("with no demand figure the project is already known to be short, so booked unless staffing",
      shortage.trade_shortage_kind("chemist", 50.0) == "booked" and shortage.trade_shortage_kind("chemist", 150.0) == "staffing")

# --- 4. warn before a multi-year step wastes hours
def _unreachable():
    raise AssertionError("the tree was scanned for a startable project when the warning could not apply")


def _warn(years=5, enabled=True, unused=True, startable=lambda: "Loom", hours=1234.0, waiting=lambda: "your hours"):
    return multi_year_hours_warning(years, enabled, unused, startable, hours, waiting)


warning = _warn()
check("a multi-year step warns, up front, when this year alone has founder-hours going to waste and something is startable",
      warning and "founder-hours" in warning and "'Loom'" in warning, warning)
# presentation: the warning names the hours at stake
check("...naming the number of hours at stake", "1,234" in warning, warning)
check("a single-year step never carries this warning", multi_year_hours_warning(1, True, True, _unreachable, 10.0, _unreachable) is None)
check("with multi_year_step_warning off, a multi-year step that would warn does not",
      multi_year_hours_warning(5, False, True, _unreachable, 10.0, _unreachable) is None)
check("with no idle hours there is nothing to warn about, and the tree is not scanned",
      multi_year_hours_warning(5, True, None, _unreachable, 10.0, _unreachable) is None)
check("with nothing startable the warning would tell the player to do something they cannot, so it does not",
      _warn(startable=lambda: None) is None)
