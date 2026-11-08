"""The producer records after the close, made from the close kernel's answer in one pass over the rows.

`closed_records(columns, answer, pooled)` is the list of records the table holds once the year has closed, one per row of the producer
columns (None for a producer that exited): the fields the close changes are taken from the answer's columns, every other field
from the record before. The records are what the rest of the game still reads (entry, the next year's plans, the save, the screens);
the columns the next phase reads are made from the same answer (`year_arrays_closed.columns_after_close`) and are given these records."""
import math
from typing import Callable, List

from . import practice


def closed_records(columns, answer, pooled: Callable[[str, str], float]) -> List[object]:
    """A producer that sat out the year (idle) has one idle year less. Any other takes its capacity, years of loss, cash target,
    histories, expected sales, last and staffed runs from the answer, the expected prices the close wrote, an idle spell the close
    began, and its crew's practice after the year's runs (`pooled(recipe_id, trade)` is the crews' pooled practice)."""
    matrices = columns.matrices
    good_ids = matrices.goods.ids
    sat_out = (columns.idle_years > 0).tolist()
    exited = answer.exited.tolist()
    capacity, losses, target = answer.new_capacity.tolist(), answer.new_losses.tolist(), answer.new_target.tolist()
    sales, last_runs, staffed = answer.new_expected_sales.tolist(), answer.new_last_runs.tolist(), answer.new_staffed.tolist()
    idle, counts = answer.new_idle.tolist(), answer.new_count.tolist()
    earnings, revenues = answer.new_earnings.tolist(), answer.new_revenues.tolist()
    writes = set(answer.written.any(axis=1).nonzero()[0].tolist())
    expected, written = answer.new_expected.tolist(), answer.written.tolist()
    slot_goods, recipe_rows = matrices.slot_goods, columns.recipe_row.tolist()
    records = []
    for row, before in enumerate(columns.records):
        if exited[row]:
            records.append(None)
            continue
        fields = before.__dict__.copy()
        if sat_out[row]:
            fields["idle_years"] = before.idle_years - 1
        else:
            fields["capacity_runs"] = capacity[row]
            fields["years_of_loss"] = losses[row]
            fields["cash_target"] = target[row]
            fields["net_earnings_history"] = tuple(earnings[row][:counts[row]])
            fields["revenue_history"] = tuple(revenues[row][:counts[row]])
            fields["expected_sales"] = sales[row]
            fields["last_runs"] = last_runs[row]
            fields["staffed_runs"] = None if math.isnan(staffed[row]) else staffed[row]
            if idle[row]:
                fields["idle_years"] = idle[row]
            if row in writes:
                prices = dict(before.expected_prices)
                for slot, column in enumerate(slot_goods[recipe_rows[row]]):
                    if column >= 0 and written[row][slot]:
                        prices[good_ids[column]] = expected[row][slot]
                fields["expected_prices"] = prices
            if before.crew_runs:
                fields["crew_runs"] = practice.crew_runs_after_year(
                    before.crew_runs, max(0.0, last_runs[row]) / max(1.0, before.workshops),
                    practice.hired_share(before.last_runs, last_runs[row]),
                    {trade: pooled(before.recipe_id, trade) for trade in before.crew_runs})
        record = object.__new__(type(before))
        record.__dict__.update(fields)
        records.append(record)
    return records
