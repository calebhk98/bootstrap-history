"""The labour market is the wage provider: prices, payroll, hiring and the
price solver all read one wage vector. Complaint 640: every check calls the wage
schedule on inputs built here; the wiring is test_wage_provider_wiring."""
QUICK_TOPIC = True
import json
import os
import tempfile
import unittest
from pathlib import Path


from sim.content import catalog
from sim.labour.api import wage_provider
from sim.prices.solve_prices_core import wage_ratios_by_trade
from sim.labour import wages

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _schedule(training_years, floor=1.0):
    return wages.WageSchedule(training_years, floor, 1.0, 0.10)


class SubsistenceFloorTests(unittest.TestCase):

    def test_nothing_pays_below_the_subsistence_floor(self):
        schedule = _schedule({"idle": 0.0})
        self.assertEqual(schedule.wage_per_hour("idle"), schedule.floor_per_hour)

    def test_priced_at_answers_another_money_value_and_leaves_the_schedule_alone(self):
        schedule = _schedule({"smith": 5.0})
        before = schedule.wage_per_hour("smith")
        priced = schedule.priced_at(3.0)
        self.assertAlmostEqual(priced.wage_per_hour("smith"), 3.0 * before)
        self.assertEqual(schedule.wage_per_hour("smith"), before)


class TrainingPremiumTests(unittest.TestCase):

    def test_longer_training_earns_more_at_equal_money(self):
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
        schedule = wages.WageSchedule(wage_provider.training_years_by_trade(registry), 2.0, 1.0, 0.05)
        self.assertGreater(schedule.wage_per_hour("test_acme_k3f9:clockmaker"), schedule.floor_per_hour)
        # A trade that states no training takes its family's median.
        self.assertEqual(schedule.wage_per_hour("test_acme_k3f9:clockmaker"), schedule.wage_per_hour("smith"))
        self.assertGreater(schedule.wage_per_hour("test_acme_k3f9:surveyor"), schedule.wage_per_hour("smith"))


if __name__ == "__main__":
    unittest.main()
