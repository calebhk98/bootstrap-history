"""The port's health report names the staple (the hunger need's largest opening good), defaults the metals to the
good backing the currency, counts the years kept, and carries diagnostics.summary of them. The rule is called on a stub agent
holding a fixture economy and its outcomes, no game."""
QUICK_TOPIC = True
import types
import unittest

from sim.economy import diagnostics
from sim.engine.economy_port_health import health_report, staple_good
from sim.tests import economy_fixture as fixture


def agent_after(years, setup=None):
    economy, outcomes = fixture.run(setup, years=years)
    return types.SimpleNamespace(economy=lambda: economy, outcomes=outcomes), economy


class HealthReportTests(unittest.TestCase):
    def test_the_report_counts_the_years_and_carries_the_summary_of_the_outcomes(self):
        agent, economy = agent_after(2)
        report = health_report(agent, metals=[fixture.METAL], staple=fixture.GRAIN)
        self.assertEqual(report["years"], 2)
        self.assertEqual(report["staple"], fixture.GRAIN)
        expected = diagnostics.summary(agent.outcomes, economy.setup, fixture.GRAIN, [fixture.METAL])
        self.assertEqual(set(report["figures"]), set(expected))
        self.assertTrue(0.0 <= report["figures"]["hunger_share"] <= 1.0)

    def test_the_staple_is_the_hunger_needs_largest_opening_good(self):
        agent, economy = agent_after(1)
        need = next(spec for spec in economy.setup.basket.needs if spec.need_id == economy.setup.hunger_need)
        self.assertIn(staple_good(agent), [good for good, _effect in need.goods])

    def test_a_report_with_no_years_kept_has_no_figures(self):
        agent, _economy = agent_after(1)
        agent.outcomes = []
        report = health_report(agent, metals=[fixture.METAL], staple=fixture.GRAIN)
        self.assertEqual((report["years"], report["figures"]), (0, {}))

    def test_metals_default_to_the_currencys_backing_good(self):
        agent, economy = agent_after(1)
        report = health_report(agent, staple=fixture.GRAIN)
        backing = economy.setup.currency.backing_good
        self.assertEqual(report["metals"], [backing] if backing else [])


if __name__ == "__main__":
    unittest.main()
