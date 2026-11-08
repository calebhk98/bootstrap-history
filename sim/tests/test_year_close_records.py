"""The producer records after the close (year_close_records.py) against the per-producer `replaced(...)` the close used to run."""
QUICK_TOPIC = True

import math
import unittest
from types import SimpleNamespace

import numpy as np

from sim.economy import practice
from sim.economy.producers import Producer
from sim.economy.replaced import replaced
from sim.economy.year_close_records import closed_records

GOODS = ("bread", "flour", "wheat")


def producer(name, **fields):
    return Producer(agent_id=name, owner="owner", recipe_id="r" + name, tile="t", capacity_runs=10.0, **fields)


def old_changes(before, row, answer, written_goods, pooled):
    """The old `_changes_of`, with the answer row read as the old loop read it."""
    expected = dict(before.expected_prices)
    for good, value in written_goods:
        expected[good] = value
    changes = dict(capacity_runs=answer["capacity"][row], years_of_loss=answer["losses"][row], cash_target=answer["target"][row],
                   expected_prices=expected, net_earnings_history=tuple(answer["earnings"][row][:answer["count"][row]]),
                   revenue_history=tuple(answer["revenues"][row][:answer["count"][row]]), expected_sales=answer["sales"][row],
                   last_runs=answer["last"][row], staffed_runs=None if math.isnan(answer["staffed"][row]) else answer["staffed"][row])
    if answer["idle"][row]:
        changes["idle_years"] = answer["idle"][row]
    if before.crew_runs:
        new_last = answer["last"][row]
        changes["crew_runs"] = practice.crew_runs_after_year(
            before.crew_runs, max(0.0, new_last) / max(1.0, before.workshops), practice.hired_share(before.last_runs, new_last),
            {trade: pooled(before.recipe_id, trade) for trade in before.crew_runs})
    return changes


class ClosedRecordsTests(unittest.TestCase):
    def test_each_kind_of_row_becomes_the_record_the_old_replacement_made(self):
        records = [producer("a", expected_prices={"bread": 2.0}), producer("b", idle_years=2), producer("c"),
                   producer("d", crew_runs={"baker": 3.0, "miller": 0.5}, last_runs=4.0, workshops=2), producer("e", idle_years=1)]
        count = len(records)
        slot_goods = np.array([[0, 1, -1]] * count)
        columns = SimpleNamespace(records=records, idle_years=np.array([0, 2, 0, 0, 1]), recipe_row=np.zeros(count, dtype=np.int64),
                                  matrices=SimpleNamespace(goods=SimpleNamespace(ids=GOODS), slot_goods=slot_goods))
        answer = SimpleNamespace(
            exited=np.array([False, False, True, False, False]), new_capacity=np.array([9.0, 0.0, 0.0, 12.0, 0.0]),
            new_losses=np.array([1, 0, 0, 2, 0]), new_target=np.array([5.0, 0.0, 0.0, 6.0, 0.0]),
            new_expected_sales=np.array([7.0, 0.0, 0.0, 8.0, 0.0]), new_last_runs=np.array([6.0, 0.0, 0.0, 9.0, 0.0]),
            new_staffed=np.array([4.0, 0.0, 0.0, np.nan, 0.0]), new_idle=np.array([0, 0, 0, 3, 0]),
            new_count=np.array([2, 0, 0, 1, 0]), new_earnings=np.array([[1.0, 2.0, 0.0]] * count),
            new_revenues=np.array([[3.0, 4.0, 0.0]] * count), written=np.array([[True, False, False]] + [[False, True, False]] * 4),
            new_expected=np.array([[2.5, 0.0, 0.0]] + [[0.0, 1.5, 0.0]] * 4))

        def pooled(recipe_id, trade):
            return {"baker": 2.0, "miller": 9.0}[trade]
        new = closed_records(columns, answer, pooled)
        arrays = dict(capacity=answer.new_capacity.tolist(), losses=answer.new_losses.tolist(), target=answer.new_target.tolist(),
                      earnings=answer.new_earnings.tolist(), revenues=answer.new_revenues.tolist(), count=answer.new_count.tolist(),
                      sales=answer.new_expected_sales.tolist(), last=answer.new_last_runs.tolist(), staffed=answer.new_staffed.tolist(),
                      idle=answer.new_idle.tolist())
        wrote = {0: [("bread", 2.5)], 1: [("flour", 1.5)], 3: [("flour", 1.5)]}
        self.assertEqual(new[0], replaced(records[0], **old_changes(records[0], 0, arrays, wrote[0], pooled)))
        self.assertEqual(new[1], replaced(records[1], idle_years=1))
        self.assertIsNone(new[2])
        self.assertEqual(new[3], replaced(records[3], **old_changes(records[3], 3, arrays, wrote[3], pooled)))
        self.assertEqual(new[4], replaced(records[4], idle_years=0))
        self.assertIsNot(new[0], records[0])


if __name__ == "__main__":
    unittest.main()
