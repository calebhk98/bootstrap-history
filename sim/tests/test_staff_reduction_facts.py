"""Complaint 168: every fall in a trade's headcount is logged with its cause, and the people the lines name are the people who
left. `log_staff_reduction` diffs the headcount against a snapshot and `log_staff_lost` writes the line; the totals are read from
the line's facts, not its words. Called over the real `StaffLedgerMixin` with a household that has these employees; the yearly
dice that remove people are the staff step's and are not run here."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.labour.labour_staff_ledger import StaffLedgerMixin
from sim.refusal import cause_of, facts_of


class Ledger(StaffLedgerMixin):
    """The ledger over a household with these `employees` and these concerns the staffing rule would shut."""

    def __init__(self, employees, stops=()):
        self.employees = dict(employees)
        self.log = []
        self._world = SimpleNamespace(
            state=SimpleNamespace(household=SimpleNamespace(log=self.log), scenario=SimpleNamespace(year=100)),
            concerns_to_close_for_staffing=lambda: list(stops), stopped_yearly_value=lambda node_ids: 10.0 * len(node_ids))

    def employed_by_trade(self):
        return dict(self.employees)


def logged_totals(ledger):
    totals = {}
    for _year, line in ledger.log:
        for trade, people in facts_of(line)["trades"].items():
            totals[trade] = totals.get(trade, 0.0) + people
    return totals


ledger = Ledger({"artisan": 20.0, "smith": 3.0, "scholar": 4.0})
start = ledger.staff_snapshot()
ledger.employees.update({"artisan": 17.5, "smith": 2.0})
ledger.log_staff_reduction("plague", start)
check("the line's facts give each trade's fall, and only the trades that fell",
      logged_totals(ledger) == {"artisan": 2.5, "smith": 1.0} and cause_of(ledger.log[0][1]) == "staff_lost", ledger.log)
before_second_year = ledger.staff_snapshot()
ledger.employees["artisan"] = 15.0
ledger.log_staff_reduction("old age", before_second_year)
check("the lines over two years add up to the headcount's fall",
      all(abs(start[trade] - ledger.employees[trade] - logged_totals(ledger).get(trade, 0.0)) < 1e-9 for trade in start), (start, ledger.employees))
quiet = Ledger({"artisan": 10.0})
quiet.log_staff_reduction("death", quiet.staff_snapshot())
check("nothing is logged when nobody left", quiet.log == [])
tiny = Ledger({"artisan": 10.0})
tiny.employees["artisan"] = 9.996
tiny.log_staff_reduction("rounding", {"artisan": 10.0})
check("a fall under half a hundredth of a person is not logged", tiny.log == [])
growing = Ledger({"artisan": 10.0})
growing.employees["artisan"] = 12.0
growing.log_staff_reduction("hiring", {"artisan": 10.0})
check("a trade that grew is not reported as lost", growing.log == [])
shutting = Ledger({"artisan": 10.0}, stops=["mill", "forge"])
shutting.employees["artisan"] = 8.0
shutting.log_staff_reduction("plague", {"artisan": 10.0})
shut_line = shutting.log[0][1]
check("a loss that leaves concerns the staffing rule will shut is its own kind and names them and what they stop earning",
      cause_of(shut_line) == "staff_lost_stops_concerns" and facts_of(shut_line)["stops"] == ["forge", "mill"]
      and facts_of(shut_line)["stops_earnings_per_year"] == 20.0, facts_of(shut_line))
