"""Complaints 167, 164 and the auto_replace_foreman part of 180: idle specialists are surfaced with their wage bill, auto_hire
replaces only the taught trades something draws on, every staff reduction is logged with its cause, and an open concern that
hangs on one person is named. The rules are called on a stub over the real `StaffLedgerMixin` (no game) and on
`replacement_wanted`; that the lines name the people who left is test_staff_reduction_facts."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.engine.seat_defaults import default_policy
from sim.workforce.staff_replacement import replacement_wanted
from sim.labour.labour_staff_ledger import StaffLedgerMixin
from sim.tests import event_stand_in

TARGET = 3.0


class Ledger(StaffLedgerMixin):
    """The mixin over a household with these `employees`, active projects and open concerns (concern -> foreman trade)."""

    def __init__(self, employees, active=None, foremen=None, taught=(), wages=None):
        self.employees = dict(employees)
        self.log = []
        self.hired = []
        self.labour_market = SimpleNamespace(quote_annual=lambda trade: (wages or {}).get(trade, 100.0))
        foremen = foremen or {}
        household = SimpleNamespace(trades_created=set(taught), log=self.log)
        projects = SimpleNamespace(active=active or {}, operating=set(foremen))
        self._world = SimpleNamespace(
            workforce=household, projects=projects, state=SimpleNamespace(household=household, scenario=SimpleNamespace(year=100)),
            nodes={node_id: {"name": node_id.title(), "lab": {}} for node_id in set(foremen) | set(active or {})},
            venture_foremen_used=lambda: {trade: 1.0 for trade in foremen.values()},
            venture_foreman=lambda node_id: (foremen[node_id], 1.0),
            concerns_to_close_for_staffing=lambda: [], stopped_yearly_value=lambda node_ids: 0.0)
        event_stand_in.stood_in(self._world)

    def employed_by_trade(self):
        return dict(self.employees)

    def employed(self, trade):
        return self.employees.get(trade, 0.0)

    def household_room(self):
        return 100.0

    def hire(self, trade, number):
        self.employees[trade] = self.employees.get(trade, 0.0) + number
        self.hired.append((trade, number))
        return True, ""


# ---- 171: auto_hire tops up only a taught trade something draws on ----------------------------------------------------
check("a taught trade nothing draws on is not topped up", replacement_wanted("machinist", 0.0, True, {}, TARGET) is None)
check("a taught trade an open concern draws on is raised to the target",
      replacement_wanted("glassblower", 0.0, True, {"glassblower": ["open concern"]}, TARGET) == TARGET)
check("a trade that is drawn on but was not taught is kept as it is, never grown",
      replacement_wanted("smith", 2.0, False, {"smith": ["project p"]}, TARGET) == 2.0)
check("a taught trade already above the target is not cut back",
      replacement_wanted("smith", 5.0, True, {"smith": ["project p"]}, TARGET) == 5.0)
check("the generic craftsmen and scholars are left to the staff target",
      replacement_wanted("artisan", 0.0, True, {"artisan": ["project p"]}, TARGET) is None
      and replacement_wanted("scholar", 0.0, True, {"scholar": ["project p"]}, TARGET) is None)

# ---- 171: idle specialists are surfaced with their wage bill ----------------------------------------------------------
idle = Ledger({"machinist": 2.0, "glassblower": 2.0, "artisan": 9.0, "potter": 0.3, "weaver": 1.0}, foremen={"mirror": "glassblower"},
              taught={"machinist"}, wages={"machinist": 50.0, "weaver": 40.0}).idle_specialists()
check("an unused machinist is listed with a wage bill and marked as taught",
      any(row["trade"] == "machinist" and row["wage_bill_per_year"] == 100.0 and row["taught_by_you"] for row in idle), idle)
check("a specialist an open concern draws on is not idle", all(row["trade"] != "glassblower" for row in idle), idle)
check("the generic craftsmen and a trade of under half a person are not idle specialists",
      {row["trade"] for row in idle} == {"machinist", "weaver"}, idle)
check("a specialist a project in hand still owes hours to is not idle",
      all(row["trade"] != "weaver" for row in Ledger({"weaver": 1.0}, active={"p": {"lab_left": {"weaver": 40.0}}}).idle_specialists()))
check("a specialist a project owes nothing more is idle again",
      any(row["trade"] == "weaver" for row in Ledger({"weaver": 1.0}, active={"p": {"lab_left": {"weaver": 0.0}}}).idle_specialists()))

# ---- 180: an open concern that hangs on one person is named; a lost foreman is replaced on request -------------------------
check("an open concern whose foreman trade has one person warns that losing them closes it",
      Ledger({"glassblower": 1.0}, foremen={"mirror": "glassblower"}).sole_supervisors()
      == [{"concern": "Mirror", "trade": "glassblower", "warning": "depends on one glassblower; losing them closes it"}])
check("two people in the foreman trade is no warning", Ledger({"glassblower": 2.0}, foremen={"mirror": "glassblower"}).sole_supervisors() == [])
lost = Ledger({}, foremen={"mirror": "glassblower"})
lost.replace_lost_foremen()
check("replace_lost_foremen hires the missing foreman and says so in the log",
      lost.hired == [("glassblower", 1)] and len(lost.log) == 1 and "auto_replace_foreman" in lost.log[0][1], (lost.hired, lost.log))
kept = Ledger({"glassblower": 1.0}, foremen={"mirror": "glassblower"})
kept.replace_lost_foremen()
check("a foreman who is still there is not hired again", kept.hired == [])
check("auto_replace_foreman is a policy, off for a player and off unattended too",
      default_policy(True)["auto_replace_foreman"] is False and default_policy(False)["auto_replace_foreman"] is False)

# ---- 168: every staff reduction is logged with its cause ---------------------------------------------------------------
shrinking = Ledger({"artisan": 10.0, "smith": 2.0})
before = shrinking.staff_snapshot()
shrinking.employees["artisan"] = 7.0
shrinking.log_staff_reduction("Test plague", before)
check("a plague trims artisans and says so in a 'you lose' line with its cause and the count",
      len(shrinking.log) == 1 and shrinking.log[0][1].startswith("you lose 3 artisans") and "Test plague" in shrinking.log[0][1], shrinking.log)
steady = Ledger({"artisan": 10.0})
steady.log_staff_reduction("death", steady.staff_snapshot())
check("nothing is logged when nobody left", steady.log == [])
