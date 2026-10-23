"""Complaint 640: the labour package is the wage provider. The payroll's hourly and annual wage and the price solver's wage
document are all read from `wage_schedule()`, the schedule's own tightness factors are the economy state's dict (so a save
carries them), the document's money conversion is the schedule's, and the tightness factors and the labour pressure are fields of
the saved state. Each function is called on a stand-in `self` or built inputs; the wage rules are test_wage_provider."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.state import EconomyState, HouseholdState, serialize_state
from sim.labour.labour_wages import WagesMixin
from sim.labour.wages import WageSchedule

DOCUMENT = {"wage_rates_denarii_per_hour": {"labourer": {"rate": 2.0}, "smith": {"rate": 5.0}}, "money_per_labour_hour": 2.0}


class StubSchedule:
    """A schedule that answers fixed numbers, so that what the labour package asks of it is what it returns."""
    training_years = {"labourer": 0.0, "smith": 5.0}

    def wage_per_hour(self, trade):
        return DOCUMENT["wage_rates_denarii_per_hour"][trade]["rate"]

    def annual_wage(self, trade):
        return 2000.0 * self.wage_per_hour(trade)

    def document(self):
        return DOCUMENT


class Wages(WagesMixin):
    """The part of a labour package whose wages come from its schedule."""

    def wage_schedule(self):
        return StubSchedule()


class PayrollAndSolverReadOneSchedule(unittest.TestCase):
    def test_the_solvers_wage_document_is_the_schedules(self):
        self.assertEqual(Wages().wage_document(), DOCUMENT)

    def test_the_hourly_wage_is_the_schedules(self):
        self.assertEqual(Wages().wage_per_hour("smith"), 5.0)

    def test_the_annual_base_wage_is_the_schedules(self):
        self.assertEqual(Wages().base_annual_wage("smith"), 10000.0)


class ScheduleDocument(unittest.TestCase):
    def test_the_documents_money_conversion_is_the_schedules_money_per_labour_hour(self):
        schedule = WageSchedule({"labourer": 0.0, "smith": 5.0}, 2.5, 1.0, 0.10)
        self.assertEqual(schedule.document()["money_per_labour_hour"], 2.5)


class TightnessFactorsLiveInTheState(unittest.TestCase):
    def test_the_opening_schedule_is_built_over_the_economy_states_own_factors(self):
        factors = {"smith": 1.2}
        built = []

        def build(civ, tightness_factors=None):
            built.append(tightness_factors)
            return types.SimpleNamespace(tightness_factors=tightness_factors, money_per_labour_hour=2.0)

        labour = Wages()
        labour._world = types.SimpleNamespace(
            state=types.SimpleNamespace(economy=types.SimpleNamespace(wage_tightness_factors=factors)),
            civ={}, build_wage_schedule=build)
        schedule = labour._opening_wage_schedule()
        self.assertIs(schedule.tightness_factors, factors)
        self.assertEqual(len(built), 1)

    def test_the_tightness_factors_are_written_into_the_saved_economy(self):
        blob = serialize_state(EconomyState(wage_tightness_factors={"smith": 1.2}))
        self.assertEqual(blob["wage_tightness_factors"], {"smith": 1.2})

    def test_the_labour_pressure_records_are_written_into_the_saved_household(self):
        blob = serialize_state(HouseholdState(capital=0.0, labour_pressure_records={"artisan": [2000.0, 100]}))
        self.assertEqual(blob["labour_pressure_records"], {"artisan": [2000.0, 100]})


if __name__ == "__main__":
    unittest.main()
