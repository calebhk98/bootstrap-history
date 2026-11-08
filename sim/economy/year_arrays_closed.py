"""The producer columns after the year's close, from the close kernel's answer instead of reading every replaced record again.

`columns_after_close(columns, producers, exited, answer)` is `ProducerColumns.build(producers, ...)` for the table the close
leaves (year_close_producers.py): the rows that exited are dropped, a producer that sat out the year (idle) has one idle year
less, and every other producer takes the fields the close changed from the answer."""
import numpy as np

from .year_arrays_producers import ProducerColumns

_ROW_FIELDS = ("recipe_row", "tile_row", "capacity_runs", "yield_factor", "years_of_loss", "cash_target", "expected_sales",
               "last_runs", "land_rent_per_run", "land_run_cap", "workshops", "idle_years", "staffed_runs", "history_count",
               "expected_prices", "earnings_history", "revenue_history")


def columns_after_close(columns: ProducerColumns, producers, exited: np.ndarray, answer, records=None) -> ProducerColumns:
    """`exited` and the answer's arrays are indexed by the rows of `columns`. `producers` is the table after the close; `records`,
    when the caller has them, are the records it holds by row of `columns` (None for an exit), and spare the lookups."""
    keep = np.nonzero(~exited)[0]
    ids = tuple(columns.ids[row] for row in keep)
    kept = {name: getattr(columns, name)[keep] for name in _ROW_FIELDS}
    sat_out = kept["idle_years"] > 0
    closed = np.nonzero(~sat_out)[0]
    source = keep[closed]
    kept["idle_years"] = np.where(sat_out, kept["idle_years"] - 1, kept["idle_years"])
    for name, new in (("capacity_runs", answer.new_capacity), ("years_of_loss", answer.new_losses),
                      ("cash_target", answer.new_target), ("expected_sales", answer.new_expected_sales),
                      ("last_runs", answer.new_last_runs), ("staffed_runs", answer.new_staffed),
                      ("history_count", answer.new_count)):
        kept[name][closed] = new[source]
    new_idle = answer.new_idle[source]
    kept["idle_years"][closed] = np.where(new_idle != 0, new_idle, kept["idle_years"][closed])
    written = answer.written[source]
    kept["expected_prices"][closed] = np.where(written, answer.new_expected[source], kept["expected_prices"][closed])
    width = answer.new_earnings.shape[1]
    wanted = np.arange(width)[None, :] < answer.new_count[source][:, None]
    for name, new in (("earnings_history", answer.new_earnings), ("revenue_history", answer.new_revenues)):
        old = kept[name]
        if old.shape[1] < width:
            old = kept[name] = np.concatenate([old, np.zeros((len(old), width - old.shape[1]))], axis=1)
        rows = old[closed]
        rows[:, :width] = np.where(wanted, new[source], 0.0)
        old[closed] = rows
    kept_records = [producers[each] for each in ids] if records is None else [records[row] for row in keep.tolist()]
    return ProducerColumns(ids, {each: position for position, each in enumerate(ids)}, kept_records,
                           matrices=columns.matrices, tiles=columns.tiles, **kept)
