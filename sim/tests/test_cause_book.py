"""Complaint 420: the reporting module keeps (cause, amount) rows for wage changes, concern closures and state notice, bounded to a
few years. The rules are plain functions over rows (sim/reporting/cause_rules.py); the module's handlers write them to the seat."""

QUICK_TOPIC = True

import unittest

from sim.reporting import cause_rules
from sim.reporting.commands import CloseCausePeriod, NoteConcernChange, NoteWageShock
from sim.reporting.module import Reporting
from sim.reporting.state import ReportingSeat
from sim.tests import module_harness


def notice_of(capacity, headcount, wealth, eminence, defiance):
    """Notice is capacity times a scale that rises with each reading."""
    return capacity * (1.0 + headcount / 1000.0 + wealth / 100000.0 + eminence / 10.0 + defiance)


def readings(wage_index=1.0, state_reach=2.0, headcount=100, wealth=1000.0, eminence=0.0, defiance=0.0):
    return {"wage_index": wage_index, "state_reach": state_reach, "headcount": headcount, "wealth": wealth,
            "eminence": eminence, "defiance": defiance}


def notice(reading):
    return notice_of(reading["state_reach"], reading["headcount"], reading["wealth"], reading["eminence"], reading["defiance"])


class AppendRow(unittest.TestCase):
    def test_a_row_is_open_until_a_period_closes_and_carries_its_extra_fields(self):
        rows = []
        cause_rules.append_row(rows, "opening", "mill", "manual", 1.0, {"revenue": 40.0, "upkeep": 15.0})
        self.assertEqual(rows, [{"year": None, "kind": "opening", "subject": "mill", "cause": "manual", "amount": 1.0,
                                 "revenue": 40.0, "upkeep": 15.0}])

    def test_a_run_that_never_closes_a_period_keeps_only_the_capped_number_of_rows(self):
        rows = []
        for count in range(cause_rules.ROWS_KEPT + 50):
            cause_rules.append_row(rows, "closure", "y", "manual", float(count))
        self.assertEqual(len(rows), cause_rules.ROWS_KEPT)
        self.assertEqual(rows[-1]["amount"], float(cause_rules.ROWS_KEPT + 49))


class NoticeSteps(unittest.TestCase):
    def test_the_parts_add_to_the_whole_change_and_name_each_reading_that_moved(self):
        before = readings()
        after = readings(state_reach=2.5, headcount=80, wealth=501000.0, eminence=3.0)
        parts = cause_rules.notice_steps(before, after, notice_of)
        self.assertAlmostEqual(sum(parts.values()), notice(after) - notice(before))
        self.assertEqual(set(parts), {cause_rules.STATE_CAUSE, "headcount", "wealth", "eminence", "defiance"})
        self.assertEqual(parts["defiance"], 0.0)
        self.assertGreater(parts["wealth"], 0.0)


class ClosePeriod(unittest.TestCase):
    def test_the_causes_sum_to_the_index_change_and_the_unnamed_part_is_its_own_cause(self):
        rows = []
        cause_rules.append_row(rows, cause_rules.WAGE, "wage_index", "a plague", -0.3)
        kept = cause_rules.close_period(rows, readings(wage_index=1.0), readings(wage_index=0.8), 101, notice_of)
        wage = cause_rules.totals_since(kept, cause_rules.WAGE, None)
        self.assertAlmostEqual(sum(wage.values()), 0.8 - 1.0)
        self.assertAlmostEqual(wage[cause_rules.UNSHOCKED_WAGE_CAUSE], 0.1)

    def test_with_no_earlier_reading_the_open_rows_are_only_stamped_with_the_year(self):
        rows = []
        cause_rules.append_row(rows, "closure", "mill", "manual", 1.0)
        kept = cause_rules.close_period(rows, None, readings(), 101, notice_of)
        self.assertEqual([(row["kind"], row["year"]) for row in kept], [("closure", 101)])

    def test_rows_older_than_the_window_are_dropped(self):
        rows = []
        cause_rules.append_row(rows, "closure", "old", "manual", 1.0)
        rows[0]["year"] = 100
        kept = cause_rules.close_period(rows, None, readings(), 100 + cause_rules.YEARS_KEPT, notice_of)
        self.assertEqual(kept, [])


class SelectRows(unittest.TestCase):
    ROWS = [{"year": 100, "kind": "wage", "subject": "wage_index", "cause": "a plague", "amount": -0.3},
            {"year": None, "kind": "closure", "subject": "mill", "cause": "by choice", "amount": 1.0}]

    def test_an_open_row_counts_as_the_year_asked_from(self):
        found = cause_rules.rows_of(self.ROWS, 103, "closure", 1)
        self.assertEqual([(row["kind"], row["year"]) for row in found], [("closure", 103)])

    def test_only_the_latest_years_of_a_kind_are_given(self):
        self.assertEqual(cause_rules.rows_of(self.ROWS, 103, "wage", 1), [])
        self.assertEqual(len(cause_rules.rows_of(self.ROWS, 103, "wage", 5)), 1)

    def test_causes_since_a_year_leave_out_the_rows_stamped_up_to_it(self):
        self.assertEqual(cause_rules.totals_since(self.ROWS, "wage", 99), {"a plague": -0.3})
        self.assertEqual(cause_rules.totals_since(self.ROWS, "wage", 100), {})


def reporting_over(views):
    return module_harness.build(Reporting, views=views, seat=ReportingSeat(), module_id="reporting")


class Handlers(unittest.TestCase):
    def test_a_wage_shock_row_names_its_cause_with_the_signed_index_change(self):
        module = reporting_over({})
        module.note_wage_shock(NoteWageShock("a plague", -0.3))
        self.assertEqual([(row["kind"], row["cause"], row["amount"]) for row in module.seat.cause_rows], [("wage", "a plague", -0.3)])

    def test_a_concern_row_carries_what_the_node_earns_and_costs_a_year(self):
        module = reporting_over({})
        module.note_concern_change(NoteConcernChange("opening", "mill", "manual", 40.0, 15.0))
        (row,) = module.seat.cause_rows
        self.assertEqual((row["kind"], row["subject"], row["cause"], row["revenue"], row["upkeep"]), ("opening", "mill", "manual", 40.0, 15.0))

    def test_closing_the_period_takes_the_readings_and_stamps_the_rows(self):
        module = reporting_over({"year": 101, "wage_index": 0.8, "state_reach": 2.0, "headcount": 100, "acting_balance": 1000.0,
                                 "standing": {"concealed": 0.0, "eminence": 0.0, "defiance": 0.0},
                                 "visible_scale": lambda headcount, wealth, eminence, defiance: 1.0})
        module.seat.cause_mark = readings(wage_index=1.0, state_reach=2.0)
        module.note_wage_shock(NoteWageShock("a plague", -0.3))
        module.close_cause_period(CloseCausePeriod())
        wage = module.causes_since(cause_rules.WAGE, None)
        self.assertAlmostEqual(sum(wage.values()), -0.2)
        self.assertEqual(module.seat.cause_mark["wage_index"], 0.8)
        self.assertEqual({row["year"] for row in module.seat.cause_rows}, {101})

    def test_the_rows_view_gives_the_acting_seats_rows_of_a_kind(self):
        module = reporting_over({"year": 103})
        module.note_wage_shock(NoteWageShock("a plague", -0.3))
        self.assertEqual([row["cause"] for row in module.cause_rows("wage", 2)], ["a plague"])
        self.assertEqual(module.cause_rows("closure", 2), [])


if __name__ == "__main__":
    unittest.main()
