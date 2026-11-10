"""Switching over the tables (`switch_year.switch_all`) gives what the plain rule on dicts gave (kept in `labour_switching_plain`):
the same workers, trainees and report, bit for bit, on random states, clearings and schools."""

QUICK_TOPIC = True

import random
import unittest

from sim.labour.market import aptitude, switching, trades
from sim.labour.market.records import LabourClearing, MarketState, School, YearInputs, YearReport
from sim.tests import labour_switching_plain as plain

REGISTRY = {"digger": {"family": "toil", "training_years": 0}, "hauler": {"family": "toil", "training_years": 0.5},
            "carver": {"family": "craft", "training_years": 3}, "smith": {"family": "craft", "training_years": 4, "difficulty": 0.3},
            "healer": {"family": "lore", "training_years": 6, "difficulty": 1.0}}
TRADES = sorted(REGISTRY)


def random_clearing(rng, area, trade):
    bids = [(rng.uniform(0.5, 6.0), rng.uniform(100, 6000)) for _ in range(rng.randint(0, 4))]
    offered = rng.choice([0.0, rng.uniform(100, 9000)])
    held = rng.choice([None, offered * rng.uniform(1.0, 1.4) + 1.0])
    return LabourClearing(trade=trade, area=area, wage=rng.uniform(0.4, 5.0), hours_offered=offered, hours_wanted=rng.choice([0.0, rng.uniform(100, 9000)]),
                          hours_hired=rng.choice([0.0, rng.uniform(0, 9000)]), hired_by_employer={}, target_wage=rng.choice([None, rng.uniform(0.4, 6.0)]),
                          hours_held=held, demand=tuple(bids))


def random_case(rng):
    bands = aptitude.band_count()
    areas = ["a%d" % each for each in range(rng.randint(1, 4))]
    workers = {area: {trade: [rng.uniform(0, 400) for _ in range(bands)] for trade in rng.sample(TRADES, rng.randint(1, len(TRADES)))} for area in areas}
    trainees = {area: {trade: [[float(rng.randint(1, 3)), [rng.uniform(0, 30) for _ in range(bands)], rng.choice([0.0, 0.3])]
                               for _ in range(rng.randint(1, 3))] for trade in rng.sample(TRADES[2:], rng.randint(0, 2))} for area in areas}
    trainees = {area: by_trade for area, by_trade in trainees.items() if by_trade}
    clearings = {(area, trade): random_clearing(rng, area, trade) for area in areas for trade in TRADES if rng.random() < 0.8}
    schools = [School("s", rng.choice(TRADES[2:]), rng.choice(areas), rng.uniform(0, 60), rng.choice([0.0, 0.4])) for _ in range(rng.randint(0, 3))]
    inputs = YearInputs(trades=trades.trade_specs(REGISTRY), bids=[], subsistence_per_worker_year={area: rng.uniform(5000, 30000) for area in areas if rng.random() < 0.9},
                        hours_per_worker_year=2000.0, discount_rate=0.05, career_years=30.0, schools=schools,
                        enterable_trades=rng.choice([None, frozenset(TRADES[1:])]))
    return MarketState(workers=workers, trainees=trainees), inputs, clearings


class SwitchingOverTablesIsTheDictRule(unittest.TestCase):
    def test_random_years(self):
        rng = random.Random(8)
        moved = 0
        for _case in range(80):
            state, inputs, clearings = random_case(rng)
            other = state.copy()
            want_report, got_report = YearReport(), YearReport()
            plain.switch_trades(other, inputs, clearings, want_report)
            switching.switch_trades(state, inputs, clearings, got_report)
            self.assertEqual(state.to_plain(), other.to_plain())
            self.assertEqual(got_report.switched, want_report.switched)
            self.assertEqual([(area, list(by_trade)) for area, by_trade in got_report.switched.items()],
                             [(area, list(by_trade)) for area, by_trade in want_report.switched.items()], "report order")
            for name in ("workers", "trainees"):
                self.assertEqual(list(getattr(state, name)), list(getattr(other, name)))
                for area in getattr(other, name):
                    self.assertEqual(list(getattr(state, name)[area]), list(getattr(other, name)[area]), "the views list pairs in the order made")
            moved += bool(want_report.switched)
        self.assertGreater(moved, 10, "the random cases should move people")


if __name__ == "__main__":
    unittest.main()
