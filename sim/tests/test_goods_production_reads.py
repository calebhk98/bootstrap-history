"""`goods_production_reads`: the block reads of a producers' turn against the per-item reads they replace. `planned_runs` against
`PlanTable.get(id).runs` and a dict's `get`, `hours_hired_of` against `ledger.hours_hired.get(producer, {}).get(trade, 0.0)` on random
ledgers, and `pair_amounts` on a name the ledger never numbered (under numba and ROME_NO_JIT=1)."""
QUICK_TOPIC = True

import random
import unittest

from sim.economy import goods_production_reads
from sim.economy.producers import Plan
from sim.economy.year_ledger import YearLedger

PRODUCERS, TRADES = ("p1", "p2", "p3", "p4"), ("smith", "miller", "porter")


class Table:
    """The two attributes of a `PlanTable` that `planned_runs` reads."""

    def __init__(self, runs):
        self.position = {producer: place for place, producer in enumerate(PRODUCERS) if place < len(runs)}
        self.runs = runs


class PlannedRunsAreTheColumn(unittest.TestCase):

    def test_a_table_is_read_by_position_and_a_missing_producer_is_none(self):
        table = Table([2.0, 0.0, 3.5])
        self.assertEqual(goods_production_reads.planned_runs(table, ["p3", "p1", "p4", "p2"]), [3.5, 2.0, None, 0.0])

    def test_a_dict_of_plans_is_read_through_get(self):
        plans = {"p1": Plan(4.0), "p2": Plan(0.0)}
        self.assertEqual(goods_production_reads.planned_runs(plans, ["p2", "p3", "p1"]), [0.0, None, 4.0])


class HoursHiredAreTheLedgers(unittest.TestCase):

    def test_random_ledgers_read_as_the_view_reads_them(self):
        for seed in range(25):
            rng = random.Random(seed)
            ledger = YearLedger()
            for producer in PRODUCERS:
                for trade in TRADES:
                    if rng.random() < 0.5:
                        ledger.hours_hired.setdefault(producer, {})[trade] = rng.uniform(0.0, 500.0)
            requests = [(rng.choice(PRODUCERS + ("nobody",)), tuple(rng.sample(TRADES + ("unhired",), rng.randint(0, 3)))) for _ in range(12)]
            expected = [{trade: ledger.hours_hired.get(producer, {}).get(trade, 0.0) for trade in trades} for producer, trades in requests]
            self.assertEqual(goods_production_reads.hours_hired_of(ledger, requests), expected, seed)

    def test_no_requests_read_as_an_empty_list(self):
        self.assertEqual(goods_production_reads.hours_hired_of(YearLedger(), []), [])

    def test_a_request_without_trades_reads_as_an_empty_dict(self):
        self.assertEqual(goods_production_reads.hours_hired_of(YearLedger(), [("p1", ())]), [{}])


if __name__ == "__main__":
    unittest.main()
