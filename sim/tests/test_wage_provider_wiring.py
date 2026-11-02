"""Complaint 640, 964: the labour package reads the economy's wage for a trade and falls back on the opening schedule before the
economy opens; the schedule's document carries its money conversion and the labour pressure is a field of the saved state.
Each function is called on a stand-in `self` or built inputs; the wage rules are test_wage_provider."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.state import serialize_state
from sim.workforce.api import WorkforceSeat
from sim.labour.labour_wages import WagesMixin
from sim.labour.wages import WageSchedule

DOCUMENT = {"wage_rates_denarii_per_hour": {"labourer": {"rate": 2.0}, "smith": {"rate": 5.0}}, "money_per_labour_hour": 2.0}


class StubSchedule:
    """A schedule that answers fixed numbers, so that what the labour package asks of it is what it returns."""
    training_years = {"labourer": 0.0, "smith": 5.0}

    def wage_per_hour(self, trade):
        return DOCUMENT["wage_rates_denarii_per_hour"][trade]["rate"]


class Wages(WagesMixin):
    """The part of a labour package whose wages come from the economy, else from its schedule."""

    def __init__(self, paid=None, unskilled=None):
        self._world = types.SimpleNamespace(
            HOURS_PER_PERSON_YEAR=2000.0, economy_unskilled_wage=lambda: unskilled,
            economy=types.SimpleNamespace(agent_wage_per_hour=lambda trade: paid))

    def wage_schedule(self):
        return StubSchedule()


class PayrollReadsTheEconomyThenTheSchedule(unittest.TestCase):
    def test_before_the_economy_opens_the_hourly_wage_is_the_schedules(self):
        self.assertEqual(Wages().wage_per_hour("smith"), 5.0)

    def test_the_economys_wage_is_the_hourly_wage_once_it_is_paid(self):
        self.assertEqual(Wages(paid=9.0, unskilled=1.0).wage_per_hour("smith"), 9.0)

    def test_the_annual_base_wage_is_a_year_of_the_hourly_wage(self):
        self.assertEqual(Wages().base_annual_wage("smith"), 10000.0)


class ScheduleDocument(unittest.TestCase):
    def test_the_documents_money_conversion_is_the_schedules_money_per_labour_hour(self):
        schedule = WageSchedule({"labourer": 0.0, "smith": 5.0}, 2.5, 1.0, 0.10)
        self.assertEqual(schedule.document()["money_per_labour_hour"], 2.5)
