"""The labour market is the wage provider: prices, payroll, hiring and the
price solver all read one wage vector, and nothing reads the book's wages."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sim.engine import catalog, data, prices as engine_prices, wage_schedule
from sim.labour import wage_provider
from sim.engine.solve_prices_core import wage_ratios_by_trade
from sim.labour import wages
from .source_dirs import engine_and_world_dirs

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _schedule(training_years, floor=1.0):
    return wages.WageSchedule(training_years, floor, 1.0, 0.10)


class TightnessTests(unittest.TestCase):

    def test_need_above_hours_raises_the_wage_every_year(self):
        schedule = _schedule({"short": 3.0, "slack": 3.0})
        history = []
        for _year in range(5):
            schedule.step({"short": 200.0, "slack": 50.0}, {"short": 100.0, "slack": 100.0})
            history.append((schedule.wage_per_hour("short"), schedule.wage_per_hour("slack")))
        short_series = [pair[0] for pair in history]
        self.assertEqual(short_series, sorted(short_series))
        self.assertLess(len(set(short_series)), len(short_series) + 1)
        self.assertGreater(short_series[-1], short_series[0])
        # Slack lowers the wage, but never below the untightened floor share.
        self.assertLessEqual(history[-1][1], history[0][1])

    def test_slack_lowers_a_skilled_wage_but_not_below_the_subsistence_floor(self):
        schedule = _schedule({"idle": 6.0})
        start = schedule.wage_per_hour("idle")
        for _year in range(200):
            schedule.step({"idle": 0.0}, {"idle": 100.0})
        self.assertLess(schedule.wage_per_hour("idle"), start)
        self.assertGreaterEqual(schedule.wage_per_hour("idle"), schedule.floor_per_hour)

    def test_equal_need_and_hours_leave_the_wage_alone(self):
        schedule = _schedule({"smith": 5.0})
        start = schedule.wage_per_hour("smith")
        for _year in range(10):
            schedule.step({"smith": 100.0}, {"smith": 100.0})
        self.assertEqual(schedule.wage_per_hour("smith"), start)


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


class EngineWageTests(unittest.TestCase):

    def setUp(self):
        from .harness import sim
        self.sim = sim(civ="rome_100ad", events=False, agent_economy=False)   # the engine's own wage schedule
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

    def test_a_tight_trade_pays_more_next_year(self):
        engine = self.sim
        before = engine.labour.wage_per_hour("smith")
        engine.state.economy.society_labour_hours["smith"] = 1.0
        engine.labour.update_wages()
        self.assertGreater(engine.labour.wage_per_hour("smith"), before)

    def test_tightness_and_labour_pressure_survive_a_save_and_load(self):
        from .harness import sim
        from sim.engine.saveload import load_state, save_state
        engine = self.sim
        engine.state.economy.wage_tightness_factors["smith"] = 1.2
        engine.labour.hire("artisan", 1)
        pressure = engine.labour.market.pressure("artisan")
        self.assertGreater(pressure, 0.0)
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "save.json")
            save_state(engine, path)
            fresh = sim(civ="rome_100ad", events=False, agent_economy=False)
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


_RUNNER = """
import json, random
from sim import simulator as S
tree, prices, nodes, wages, goods = S.load()
_lab, order, _b = S.load_strategy("recommended", nodes, tree["meta"]["goal_node"])
engine = S.Sim(nodes, order, random.Random(1), events=False, manual=True, civ=S.load_civ("rome_100ad"))
print(json.dumps({"labourer": engine.labour.wage_per_hour("labourer"),
                  "smith": engine.labour.wage_per_hour("smith"), "annual": engine.labour.market.quote_annual("smith")}))
"""


class NoBookWagesTests(unittest.TestCase):

    def test_engine_runs_with_no_wage_book_on_disk(self):
        result = subprocess.run([sys.executable, "-c", _RUNNER], capture_output=True, text=True,
                                timeout=600, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr[-800:])
        figures = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertGreater(figures["smith"], figures["labourer"])
        self.assertGreater(figures["annual"], 0)

    def test_only_the_wage_document_shape_names_the_wage_key(self):
        # The solver reads wages through a document in the book's shape, so
        # its builder and reader name the key; the loader must not.
        offenders = []
        for directory in engine_and_world_dirs():
            for name in sorted(os.listdir(directory)):
                if name.endswith(".py"):
                    with open(os.path.join(directory, name), encoding="utf-8") as source:
                        if "wage_rates_denarii_per_hour" in source.read():
                            offenders.append(name)
        self.assertLessEqual(set(offenders), {"prices.py", "solve_prices_core.py", "wages.py"})


if __name__ == "__main__":
    unittest.main()
