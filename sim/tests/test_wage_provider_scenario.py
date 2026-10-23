"""Scenarios (Complaint 640): the wage provider in a built game: solver and payroll read one wage, tightness and pressure
survive a save and load, and the start is at equilibrium. That no source outside the wage document names the wage key is in
test_wage_provider; the wage rules are there too (a tight trade paying more is test_need_above_hours_raises_the_wage_every_year there)."""
import os
import tempfile
import unittest

from sim.engine import prices as engine_prices
from sim.engine.solve_prices_core import wage_ratios_by_trade


class EngineWageTests(unittest.TestCase):

    def setUp(self):
        from .harness import sim, unopened_sim
        self.sim = unopened_sim(civ="rome_100ad", events=False)   # legacy: the engine's own wage schedule
        self.sim._demographic_recovery(101)

    def test_solver_and_payroll_read_the_same_wage(self):
        engine = self.sim
        engine.state.economy.wage_tightness_factors["smith"] = 1.3
        ratios = wage_ratios_by_trade(engine.labour.wage_document())
        for trade in ("labourer", "smith", "scribe"):
            self.assertAlmostEqual(
                ratios[trade], engine.labour.wage_per_hour(trade) / engine.labour.wage_per_hour("labourer"))
        # Payroll's annual figure is that same hourly wage over a working year.
        self.assertAlmostEqual(
            engine.labour.market.unscarce_annual("smith"),
            engine.labour.wage_per_hour("smith") * engine.HOURS_PER_PERSON_YEAR
            * engine.labour.market.cost_factors("smith")["weighted"]
            * engine.price_index * engine.wage_index)
        # The price solver's money conversion is the schedule's coin-anchored rate.
        self.assertEqual(engine_prices.denarii_per_labour_hour(engine.labour.wage_document()),
                         engine.labour.wage_schedule().money_per_labour_hour)

    def test_tightness_and_labour_pressure_survive_a_save_and_load(self):
        from .harness import sim, unopened_sim
        from sim.engine.saveload import load_state, save_state
        engine = self.sim
        engine.state.economy.wage_tightness_factors["smith"] = 1.2
        engine.labour.hire("artisan", 1)
        pressure = engine.labour.market.pressure("artisan")
        self.assertGreater(pressure, 0.0)
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "save.json")
            save_state(engine, path)
            fresh = unopened_sim(civ="rome_100ad", events=False)   # legacy: the engine's own wage schedule
            load_state(fresh, path)
        self.assertEqual(fresh.labour.wage_schedule().tightness_factors["smith"], 1.2)
        self.assertAlmostEqual(fresh.labour.market.pressure("artisan"), pressure)

    def test_start_is_at_equilibrium(self):
        engine = self.sim
        engine.labour.update_wages()
        hours = engine.state.economy.society_labour_hours
        total = sum(hours.values())
        for trade, factor in engine.state.economy.wage_tightness_factors.items():
            if hours.get(trade, 0.0) > 0.01 * total:
                self.assertAlmostEqual(factor, 1.0, places=3, msg=trade)


if __name__ == "__main__":
    unittest.main()
