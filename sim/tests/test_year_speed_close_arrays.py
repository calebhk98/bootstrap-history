"""Numba port item 0b: the producer columns the close hands on (`columns_after_close`) are the columns read fresh from the table
the close leaves. The close's answer is made up at random for a random built economy, applied to the records the way
year_close_producers applies it (the fields it changes, an exit removing the row, an idle producer one idle year less), and the
columns built from those records are the reference. No game is run."""

QUICK_TOPIC = True

import random
import unittest
from dataclasses import replace

import numpy as np

from sim.economy.close_run import CloseAnswer
from sim.economy.year_arrays import YearArrays
from sim.economy.year_arrays_closed import columns_after_close
from sim.tests.year_close_fixture import economy_of


def random_answer(columns, rng):
    answer = CloseAnswer.empty(columns)
    count, slots = columns.expected_prices.shape
    width = answer.new_earnings.shape[1]
    answer.new_capacity[:] = rng.uniform(0, 50, count)
    answer.new_losses[:] = rng.integers(0, 4, count)
    answer.new_target[:] = rng.uniform(0, 9, count)
    answer.new_expected_sales[:] = rng.uniform(0, 30, count)
    answer.new_last_runs[:] = rng.uniform(0, 30, count)
    answer.new_staffed[:] = np.where(rng.random(count) < 0.3, np.nan, rng.uniform(0, 30, count))
    answer.new_idle[:] = np.where(rng.random(count) < 0.2, rng.integers(1, 4, count), 0)
    answer.new_count[:] = rng.integers(1, width + 1, count)
    answer.new_expected[:] = rng.uniform(0.5, 9, (count, slots))
    answer.written[:] = (rng.random((count, slots)) < 0.4) & (columns.matrices.slot_goods[columns.recipe_row] >= 0)     # only a slot the recipe has
    answer.new_earnings[:] = rng.uniform(-5, 5, (count, width))
    answer.new_revenues[:] = rng.uniform(0, 20, (count, width))
    answer.exited[:] = rng.random(count) < 0.15
    return answer


def apply_to_records(columns, producers, answer):
    """What year_close_producers does to the records for the answer's rows (crews are not columns, so left out)."""
    for row, producer_id in enumerate(columns.ids):
        producer = producers[producer_id]
        if producer.idle_years > 0:
            producers[producer_id] = replace(producer, idle_years=producer.idle_years - 1)
            continue
        if answer.exited[row]:
            del producers[producer_id]
            continue
        expected = dict(producer.expected_prices)
        for slot, column in enumerate(columns.matrices.slot_goods[columns.recipe_row[row]]):
            if column >= 0 and answer.written[row, slot]:
                expected[columns.matrices.goods.ids[column]] = answer.new_expected[row, slot]
        count = int(answer.new_count[row])
        staffed = answer.new_staffed[row]
        producers[producer_id] = replace(
            producer, capacity_runs=answer.new_capacity[row], years_of_loss=int(answer.new_losses[row]),
            cash_target=answer.new_target[row], expected_prices=expected, expected_sales=answer.new_expected_sales[row],
            last_runs=answer.new_last_runs[row], staffed_runs=None if np.isnan(staffed) else staffed,
            idle_years=int(answer.new_idle[row]) or producer.idle_years,
            net_earnings_history=tuple(answer.new_earnings[row, :count]), revenue_history=tuple(answer.new_revenues[row, :count]))


class ColumnsAfterTheClose(unittest.TestCase):
    def test_they_are_the_columns_of_the_table_the_close_leaves(self):
        for seed in range(6):
            setup, record, view, _ledger, area_map = economy_of(seed)
            producers = dict(record.producers)
            for index, producer_id in enumerate(sorted(producers)):
                if index % 7 == 3:
                    producers[producer_id] = replace(producers[producer_id], idle_years=2)
            record.producers.update(producers)
            arrays = YearArrays.build(setup, record, area_map, view)
            columns = arrays.producers
            answer = random_answer(columns, np.random.default_rng(seed))
            answer.exited[columns.idle_years > 0] = False
            apply_to_records(columns, record.producers, answer)
            after = columns_after_close(columns, record.producers, answer.exited, answer)
            fresh = type(columns).build(record.producers, columns.matrices, columns.tiles)
            self.assertEqual(after.ids, fresh.ids)
            self.assertEqual(after.row, fresh.row)
            for name in ("recipe_row", "tile_row", "capacity_runs", "yield_factor", "years_of_loss", "cash_target", "expected_sales",
                         "last_runs", "land_rent_per_run", "land_run_cap", "workshops", "idle_years", "staffed_runs", "history_count",
                         "expected_prices"):
                np.testing.assert_array_equal(getattr(after, name), getattr(fresh, name), name)
            for name in ("earnings_history", "revenue_history"):
                shared = min(getattr(after, name).shape[1], getattr(fresh, name).shape[1])
                np.testing.assert_array_equal(getattr(after, name)[:, :shared], getattr(fresh, name)[:, :shared], name)
            for position, producer_id in enumerate(after.ids):
                self.assertIs(after.records[position], record.producers[producer_id])

    def test_the_old_columns_are_left_as_they_were(self):
        setup, record, view, _ledger, area_map = economy_of(1)
        columns = YearArrays.build(setup, record, area_map, view).producers
        before = columns.capacity_runs.copy()
        answer = random_answer(columns, np.random.default_rng(1))
        columns_after_close(columns, record.producers, answer.exited, answer)
        np.testing.assert_array_equal(columns.capacity_runs, before)


if __name__ == "__main__":
    unittest.main()
