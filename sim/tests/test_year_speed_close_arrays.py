"""The producer table the close leaves (`producer_close_write.write_close`) is the table the per-record replacements made. The close's answer is made up at random for a random built economy, applied to the records the way
the close used to apply it (the fields it changes, an exit removing the row, an idle producer one idle year less, the crew's practice),
and to the store by `write_close`. The records and the columns read from both are compared. No game is run."""

QUICK_TOPIC = True

import random
import unittest
from dataclasses import replace

import numpy as np

from sim.economy.close_run import CloseAnswer
from sim.economy.year_arrays import YearArrays
from sim.economy import practice
from sim.economy.producer_close_write import write_close
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


def pooled(recipe_id, trade):
    return 3.0


def apply_to_records(columns, producers, answer):
    """What year_close_producers does to the records for the answer's rows ."""
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
        if producer.crew_runs:
            last = float(answer.new_last_runs[row])
            producers[producer_id] = replace(producers[producer_id], crew_runs=practice.crew_runs_after_year(
                producer.crew_runs, max(0.0, last) / max(1.0, producer.workshops), practice.hired_share(producer.last_runs, last),
                {trade: pooled(producer.recipe_id, trade) for trade in producer.crew_runs}))


class TheTableAfterTheClose(unittest.TestCase):
    def test_it_is_the_table_the_record_replacements_make(self):
        for seed in range(6):
            setup, record, view, _ledger, area_map = economy_of(seed)
            for index, producer_id in enumerate(sorted(record.producers)):
                if index % 7 == 3:
                    record.producers[producer_id] = replace(record.producers[producer_id], idle_years=2)
                if index % 5 == 1:
                    record.producers[producer_id] = replace(record.producers[producer_id], crew_runs={"farmer": 2.0, "smith": 0.5})
            arrays = YearArrays.build(setup, record, area_map, view)
            columns = arrays.producers
            answer = random_answer(columns, np.random.default_rng(seed))
            answer.exited[columns.idle_years > 0] = False
            reference = dict(record.producers)
            apply_to_records(columns, reference, answer)
            for row in np.nonzero(answer.exited)[0].tolist():
                del record.producers[columns.ids[row]]
            write_close(record.producers, columns, answer, pooled)
            self.assertEqual(dict(record.producers), reference)
            after = type(columns).of(record.producers, columns.matrices, columns.tiles)
            fresh = type(columns).build(reference, columns.matrices, columns.tiles)
            self.assertEqual(after.ids, fresh.ids)
            for name in ("recipe_row", "tile_row", "capacity_runs", "yield_factor", "years_of_loss", "cash_target", "expected_sales",
                         "last_runs", "land_rent_per_run", "land_run_cap", "workshops", "idle_years", "staffed_runs", "history_count",
                         "expected_prices", "earnings_history", "revenue_history", "hours_scale"):
                np.testing.assert_array_equal(getattr(after, name), getattr(fresh, name), name)


if __name__ == "__main__":
    unittest.main()
