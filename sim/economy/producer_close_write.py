"""What the year's close writes into the producer table, as block writes from the close kernel's answer.

`write_close(store, columns, answer, pooled)` changes the rows of the producers that did not exit: a producer that sat out the year
(idle) has one idle year less; any other takes its capacity, years of loss, cash target, histories, expected sales, last and
staffed runs from the answer, the expected prices the close wrote, an idle spell the close began, and its crew's practice after the
year's runs (`pooled(recipe_id, trade)` is the crews' pooled practice). A row whose producer exited is dead in the store already
(the exit removed it), and the rows of `columns` are the store's rows because nothing compacts the store during the close."""
import numpy as np

from . import practice
from .producer_store import ProducerStore


def write_close(store: ProducerStore, columns, answer, pooled) -> None:
    """The closed year's figures written into the table's columns for every producer still in it."""
    alive = ~answer.exited
    sat_out = (columns.idle_years > 0) & alive
    ran = (columns.idle_years <= 0) & alive
    source = np.nonzero(ran)[0]
    rows = columns.rows[source]
    table = store.table
    table.idle_years[columns.rows[sat_out]] = columns.idle_years[sat_out] - 1
    table.capacity_runs[rows] = answer.new_capacity[source]
    table.years_of_loss[rows] = answer.new_losses[source]
    table.cash_target[rows] = answer.new_target[source]
    table.expected_sales[rows] = answer.new_expected_sales[source]
    table.last_runs[rows] = answer.new_last_runs[source]
    table.staffed_runs[rows] = answer.new_staffed[source]
    new_idle = answer.new_idle[source]
    table.idle_years[rows] = np.where(new_idle != 0, new_idle, table.idle_years[rows])
    _write_histories(store, rows, answer, source)
    _write_expected_prices(store, columns, rows, answer, source)
    _write_crews(store, columns, rows, answer, source, pooled)
    store.written(columns.rows[alive])


def _write_histories(store: ProducerStore, rows: np.ndarray, answer, source: np.ndarray) -> None:
    counts = answer.new_count[source]
    width = int(counts.max()) if len(counts) else 0
    for column in ("earnings_history", "revenue_history"):
        if width > getattr(store.table, column).shape[1]:
            store._widen(column, width)
    table = store.table
    table.earnings_count[rows] = counts
    table.revenue_count[rows] = counts
    for column, new in (("earnings_history", answer.new_earnings), ("revenue_history", answer.new_revenues)):
        held = getattr(table, column)
        held[rows, :] = 0.0
        held[rows, :width] = new[source, :width]


def _write_expected_prices(store: ProducerStore, columns, rows: np.ndarray, answer, source: np.ndarray) -> None:
    """Each price the close wrote (`answer.written`) replaces the producer's expectation for that slot's good, or is added after the
    ones it holds; slots in order, so a new good goes where the mapping would have put it."""
    matrices = columns.matrices
    store_number_of_column = store.names["goods"].admit(matrices.goods.ids)
    slots = matrices.slot_goods[columns.recipe_row[source]]
    written, expected = answer.written[source], answer.new_expected[source]
    for slot in range(slots.shape[1]):
        chosen = np.nonzero(written[:, slot] & (slots[:, slot] >= 0))[0]
        if not len(chosen):
            continue
        targets = rows[chosen]
        good = store_number_of_column[slots[chosen, slot]]
        count = store.table.price_count[targets]
        match = (store.table.price_good[targets] == good[:, None]) & (np.arange(store.table.price_good.shape[1])[None, :] < count[:, None])
        has = match.any(axis=1)
        place = np.where(has, match.argmax(axis=1), count)
        if int(place.max()) + 1 > store.table.price_good.shape[1]:
            store._widen("price_good", int(place.max()) + 1)
        table = store.table
        table.price_good[targets, place] = good
        table.price_value[targets, place] = expected[chosen, slot]
        table.price_count[targets] = np.where(has, count, count + 1)


def _write_crews(store: ProducerStore, columns, rows: np.ndarray, answer, source: np.ndarray, pooled) -> None:
    """A crew that has practised carries the year's runs (`practice.crew_runs_after_year`), for the producers that have a crew."""
    crewed = np.nonzero(store.table.crew_count[rows] > 0)[0]
    recipe_names = store.names["recipes"].name_list
    for place in crewed.tolist():
        row, position = int(rows[place]), int(source[place])
        crew = store.crew_of(row)
        recipe_id = recipe_names[store.table.recipe[row]]
        runs_now = float(answer.new_last_runs[position])
        store.write_crew(row, practice.crew_runs_after_year(
            crew, max(0.0, runs_now) / max(1.0, float(store.table.workshops[row])),
            practice.hired_share(float(columns.last_runs[position]), runs_now), {trade: pooled(recipe_id, trade) for trade in crew}))
