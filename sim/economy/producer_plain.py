"""The producer table written as plain data a column at a time (`ProducerStore.to_plain`)."""
from typing import Dict, List

from .producer_rows import SCALAR_FLOATS, SCALAR_INTS


def _pairs(names: List[str], numbers, values, counts) -> List[Dict[str, float]]:
    """One {name: value} dict per row from its first `count` (number, value) cells."""
    return [{names[number]: value for number, value in zip(row_numbers[:count], row_values[:count])}
            for row_numbers, row_values, count in zip(numbers, values, counts)]


def _unset_as_none(column: List[float]) -> List[object]:
    return [None if value != value else value for value in column]


def plain_rows(store, rows, field_names) -> List[Dict[str, object]]:
    """The fields (`field_names`, in that order) of the producers in `rows` as plain Python values, as `ProducerStore._fields` gives
    them one row at a time."""
    table, names = store.table, store.names
    chosen = rows
    earnings_counts, revenue_counts = table.earnings_count[chosen].tolist(), table.revenue_count[chosen].tolist()
    columns = {
        "agent_id": [store.ids[row] for row in chosen.tolist()],
        "owner": [names["owners"].name_list[number] for number in table.owner[chosen].tolist()],
        "recipe_id": [names["recipes"].name_list[number] for number in table.recipe[chosen].tolist()],
        "tile": [names["tiles"].name_list[number] for number in table.tile[chosen].tolist()],
        "expected_prices": _pairs(names["goods"].name_list, table.price_good[chosen].tolist(), table.price_value[chosen].tolist(),
                                  table.price_count[chosen].tolist()),
        "land_run_cap": _unset_as_none(table.land_run_cap[chosen].tolist()),
        "staffed_runs": _unset_as_none(table.staffed_runs[chosen].tolist()),
        "net_earnings_history": [tuple(each[:count]) for each, count in zip(table.earnings_history[chosen].tolist(), earnings_counts)],
        "revenue_history": [tuple(each[:count]) for each, count in zip(table.revenue_history[chosen].tolist(), revenue_counts)],
        "crew_runs": _pairs(names["trades"].name_list, table.crew_trade[chosen].tolist(), table.crew_units[chosen].tolist(),
                            table.crew_count[chosen].tolist()),
    }
    for name in SCALAR_FLOATS + SCALAR_INTS:
        columns[name] = getattr(table, name)[chosen].tolist()
    return [dict(zip(field_names, values)) for values in zip(*[columns[name] for name in field_names])]
