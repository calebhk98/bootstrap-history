"""The port's health report names the staple (the hunger need's largest opening good), defaults the metals to the
good backing the currency, counts the years kept, and hands the outcomes to `diagnostics.summary`. The rule is called on
a stand-in agent whose economy is written out here; the summary and the opening quantities are recorders."""
QUICK_TOPIC = True
import types
import unittest
from unittest import mock

from sim.engine import economy_port_health
from sim.engine.economy_port_health import health_report, staple_good

OPENING = {"grain_kg": 5.0, "porridge_kg": 9.0, "metal_kg": 1.0}


def agent_with(outcomes, backing_good="metal_kg"):
    need = types.SimpleNamespace(need_id="food", goods=(("grain_kg", 1.0), ("porridge_kg", 1.0)))
    setup = types.SimpleNamespace(basket=types.SimpleNamespace(needs=(need,)), hunger_need="food",
                                  currency=types.SimpleNamespace(backing_good=backing_good))
    economy = types.SimpleNamespace(setup=setup)
    return types.SimpleNamespace(economy=lambda: economy, outcomes=outcomes)


def report_of(agent, **options):
    calls = []

    def summary(outcomes, setup, staple, metals):
        calls.append((list(outcomes), staple, list(metals)))
        return {"hunger_share": 0.25}

    with mock.patch.object(economy_port_health.diagnostics, "summary", summary), \
            mock.patch.object(economy_port_health, "opening_quantities", lambda economy: OPENING):
        return health_report(agent, **options), calls


class HealthReportTests(unittest.TestCase):
    def test_the_report_counts_the_years_and_carries_the_summary_of_the_outcomes(self):
        report, calls = report_of(agent_with(["year one", "year two"]), metals=["gold"], staple="grain_kg")
        self.assertEqual((report["years"], report["staple"], report["figures"]), (2, "grain_kg", {"hunger_share": 0.25}))
        self.assertEqual(calls, [(["year one", "year two"], "grain_kg", ["gold"])])

    def test_the_staple_is_the_hunger_needs_largest_opening_good(self):
        with mock.patch.object(economy_port_health, "opening_quantities", lambda economy: OPENING):
            self.assertEqual(staple_good(agent_with([])), "porridge_kg")

    def test_a_report_with_no_years_kept_has_no_figures(self):
        report, calls = report_of(agent_with([]), metals=["gold"], staple="grain_kg")
        self.assertEqual((report["years"], report["figures"], calls), (0, {}, []))

    def test_metals_default_to_the_currencys_backing_good(self):
        report, _calls = report_of(agent_with(["year"]), staple="grain_kg")
        self.assertEqual(report["metals"], ["metal_kg"])

    def test_a_currency_with_no_backing_good_has_no_default_metals(self):
        report, _calls = report_of(agent_with(["year"], backing_good=None), staple="grain_kg")
        self.assertEqual(report["metals"], [])


if __name__ == "__main__":
    unittest.main()
