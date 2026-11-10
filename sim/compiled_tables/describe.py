"""One row of a table as names and values, for debugging and for the text of an error."""
from typing import Dict, Optional

from .ids import IdTable
from .spec import TableSpec


def describe_row(spec: TableSpec, table, row: int, id_tables: Optional[Dict[str, IdTable]] = None) -> dict:
    """{column: value} for one row; a column marked as holding ids shows the name its id table gives the number."""
    if not 0 <= row < int(table.row_count[0]):
        raise IndexError("row %d is outside the %d rows in use" % (row, int(table.row_count[0])))
    described = {}
    for column in spec.columns:
        value = getattr(table, column.name)[row].item()
        if column.ids is not None and id_tables is not None:
            value = id_tables[column.ids].describe(value)
        described[column.name] = value
    return described
