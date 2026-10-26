"""The labour market is the wage provider: prices, payroll, hiring and the
price solver all read one wage vector. Complaint 640: every check calls the wage
schedule on inputs built here; the wiring is test_wage_provider_wiring."""
QUICK_TOPIC = True
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sim.prices import prices as engine_prices

from sim.engine import catalog, data, wage_schedule
from sim.labour import wage_provider
from sim.prices.solve_prices_core import wage_ratios_by_trade
from sim.labour import wages

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _schedule(training_years, floor=1.0, tightness=None):
    return wages.WageSchedule(training_years, floor, 1.0, 0.10, tightness_factors=tightness)


class TightnessTests(unittest.TestCase):

    def test_need_above_hours_raises_a_trades_tightness_and_slack_lowers_it(self):
        schedule = _schedule({"short": 3.0, "slack": 3.0, "level": 3.0})
        schedule.tightness_factors.update({"short": 1.0, "slack": 1.0, "level": 1.0})
        schedule.step({"short": 200.0, "slack": 50.0, "level": 100.0},
                      {"short": 100.0, "slack": 100.0, "level": 100.0})
        self.assertGreater(schedule.tightness_factors["short"], 1.0)
        self.assertLess(schedule.tightness_factors["slack"], 1.0)
        self.assertEqual(schedule.tightness_factors["level"], 1.0)

    def test_a_trade_with_no_hours_asked_or_offered_is_left_alone(self):
        schedule = _schedule({"smith": 5.0})
        schedule.step({},
                      {})
        self.assertEqual(schedule.tightness_factors["smith"], 1.0)

    def test_slack_lowers_a_skilled_wage_but_not_below_the_subsistence_floor(self):
        untightened = _schedule({"idle": 6.0})
        slack = _schedule({"idle": 6.0}, tightness={"idle": 0.9})
        idle_for_ages = _schedule({"idle": 6.0}, tightness={"idle": 1e-6})
        self.assertLess(slack.wage_per_hour("idle"), untightened.wage_per_hour("idle"))
        self.assertEqual(idle_for_ages.wage_per_hour("idle"), idle_for_ages.floor_per_hour)

    def test_a_tight_trade_pays_more_than_an_untightened_one(self):
        self.assertGreater(_schedule({"smith": 5.0}, tightness={"smith": 1.2}).wage_per_hour("smith"),
                           _schedule({"smith": 5.0}).wage_per_hour("smith"))


class TrainingPremiumTests(unittest.TestCase):

    def test_longer_training_earns_more_at_equal_tightness(self):
        schedule = _schedule({"untrained": 0.0, "short": 2.0, "long": 8.0})
        self.assertEqual(schedule.wage_per_hour("untrained"), schedule.floor_per_hour)
        self.assertGreater(schedule.wage_per_hour("short"), schedule.wage_per_hour("untrained"))
        self.assertGreater(schedule.wage_per_hour("long"), schedule.wage_per_hour("short"))

    def test_premium_repays_the_years_forgone(self):
        discount = 0.1
        career = 30.0
        premium = wages.training_premium(5.0, discount, career)
        import math
        unskilled = (1 - math.exp(-discount * career)) / discount
        skilled = premium * (math.exp(-discount * 5.0) - math.exp(-discount * career)) / discount
        self.assertAlmostEqual(unskilled, skilled, places=9)

    def test_a_higher_discount_rate_demands_a_bigger_premium(self):
        self.assertGreater(wages.training_premium(5.0, 0.2), wages.training_premium(5.0, 0.05))


class ProviderTests(unittest.TestCase):

    def test_a_mod_trade_gets_a_wage_with_no_wage_table_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data/production").mkdir(parents=True)
            (root / "data/production/base.json").write_text('{"materials": {}}')
            (root / "data/world").mkdir(parents=True)
            (root / "data/world/trades.json").write_text(json.dumps({"trades": {
                "labourer": {"family": "labour", "training_years": 0},
                "smith": {"family": "craft", "training_years": 5},
                "potter": {"family": "craft", "training_years": 3}}}))
            mod = root / "mods/acme"
            (mod / "data/world").mkdir(parents=True)
            (mod / "mod.json").write_text(json.dumps({
                "id": "test_acme_k3f9", "name": "Acme", "version": "1", "dependencies": [], "conflicts": []}))
            (mod / "data/world/trades.json").write_text(json.dumps({"trades": {
                "test_acme_k3f9:clockmaker": {"family": "craft"},
                "test_acme_k3f9:surveyor": {"family": "craft", "training_years": 9}}}))
            registry = catalog.load_trade_registry(str(root), mods_dir=str(root / "mods"))
        schedule = wage_schedule.build_schedule(registry, data.load_civ("rome_100ad"))
        self.assertGreater(schedule.wage_per_hour("test_acme_k3f9:clockmaker"), schedule.floor_per_hour)
        # A trade that states no training takes its family's median.
        self.assertEqual(schedule.wage_per_hour("test_acme_k3f9:clockmaker"), schedule.wage_per_hour("smith"))
        self.assertGreater(schedule.wage_per_hour("test_acme_k3f9:surveyor"), schedule.wage_per_hour("smith"))


if __name__ == "__main__":
    unittest.main()
