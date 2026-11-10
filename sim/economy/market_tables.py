"""The market memory's numberings and tables in one place (`MarketTables`): who is market number 7, and where its figures are.

Six `IdTable`s: goods and trades (the first part of a market's name), areas (the second part, goods areas and labour areas
alike), quote kinds, goods markets (`good|area`) and labour markets (`trade|labour area`). A market is numbered the first time
a figure is written for it, or when the areas are drawn (`admit_goods_markets`), in sorted batches; a game saved and loaded
keeps its numbers (`state`, `from_state`). Row `r` of a table is market `r` of its numbering, so the table has exactly as many
rows in use as its numbering has names.

The stores (`market_store.py`) and the kernels (`market_table_kernels.py`) work on `goods_table` and `labour_table`. Anything
that replaces a table or a numbering (`install_goods_markets`, `load_state`) bumps `generation`, and a write through a store bumps `writes`;
cached readers compare both."""
from typing import Dict, Iterable, List, Optional

import numpy

from sim.compiled_tables.growth import reserve_rows
from sim.compiled_tables.ids import IdTable

from .market_table_specs import (GOODS_MARKETS, KEY_SEPARATOR, LABOUR_MARKETS, STORE_COUNT, GoodsMarkets, LabourMarkets)

_FLOAT_COLUMNS_OF_GOODS = ("price", "usual_price", "cleared_price", "volume_weight")
_FIRST_CAPACITY = 64


def blank_rows(table, first_row: int, last_row: int, float_columns) -> None:
    """Rows `first_row .. last_row - 1` hold nothing: NaN in the float columns, 0 elsewhere."""
    for column in table._fields:
        if column in ("row_count", "capacity"):
            continue
        getattr(table, column)[first_row:last_row] = numpy.nan if column in float_columns else 0


class MarketTables:
    """The numberings, the two tables, and the per-store bookkeeping the stores' mappings need."""

    def __init__(self) -> None:
        self.goods = IdTable("good")
        self.trades = IdTable("trade")
        self.areas = IdTable("area")
        self.kinds = IdTable("quote kind")
        self.goods_markets = IdTable("goods market")
        self.labour_markets = IdTable("labour market")
        self.goods_table = GOODS_MARKETS.new_table(GoodsMarkets, _FIRST_CAPACITY)
        self.labour_table = LABOUR_MARKETS.new_table(LabourMarkets, _FIRST_CAPACITY)
        self.next_order = numpy.zeros(STORE_COUNT, dtype=numpy.int64)       # per store: the entry number the next market gets
        self.member_count = numpy.zeros(STORE_COUNT, dtype=numpy.int64)     # per store: how many markets are in it
        self.generation = 0
        self.writes = 0          # bumped by every write to a figure through a store (`market_store.py`): a reader's copy of a column is stale when it changes
        self.rebind()

    def rebind(self) -> None:
        """Re-read the name-to-row dicts the stores look markets up in (after a numbering is replaced) and note the change."""
        self.goods_numbers: Dict[str, int] = self.goods_markets.numbers
        self.labour_numbers: Dict[str, int] = self.labour_markets.numbers
        self.generation += 1

    def _admit(self, keys: Iterable[str], labour: bool) -> None:
        """Number the markets not yet numbered (sorted among themselves) and give their rows a blank, correctly named start."""
        numbering = self.labour_markets if labour else self.goods_markets
        first_table = self.trades if labour else self.goods
        new = sorted({key for key in keys if key not in numbering.numbers})
        if not new:
            return
        table, spec_float = (self.labour_table, ("wage",)) if labour else (self.goods_table, _FLOAT_COLUMNS_OF_GOODS)
        before = len(numbering)
        table = reserve_rows(table, len(new))
        numbering.admit(new)
        parts = [key.partition(KEY_SEPARATOR) for key in new]
        firsts = first_table.admit([part[0] for part in parts])
        areas = self.areas.admit([part[2] for part in parts])
        blank_rows(table, before, before + len(new), spec_float)
        table.first[before:before + len(new)] = firsts
        table.area[before:before + len(new)] = areas
        table.row_count[0] = before + len(new)
        if labour:
            self.labour_table = table
        else:
            self.goods_table = table
        self.generation += 1

    def admit_goods_markets(self, keys: Iterable[str]) -> None:
        """Number the goods markets (`good|area`) not yet numbered, as one sorted batch."""
        self._admit(keys, labour=False)

    def admit_labour_markets(self, keys: Iterable[str]) -> None:
        """Number the labour markets (`trade|labour area`) not yet numbered, as one sorted batch."""
        self._admit(keys, labour=True)

    def goods_row_for_write(self, key: str) -> int:
        """The row of a goods market, numbering it first when it is new."""
        row = self.goods_numbers.get(key)
        if row is None:
            self._admit((key,), labour=False)
            row = self.goods_numbers[key]
        return row

    def labour_row_for_write(self, key: str) -> int:
        """The row of a labour market, numbering it first when it is new."""
        row = self.labour_numbers.get(key)
        if row is None:
            self._admit((key,), labour=True)
            row = self.labour_numbers[key]
        return row

    def kind_number(self, kind: str) -> int:
        """The number of a quote kind, numbering it first when it is new."""
        number = self.kinds.numbers.get(kind)
        return int(self.kinds.admit((kind,))[0]) if number is None else number

    def install_goods_markets(self, numbering: IdTable, table) -> None:
        """Replace the goods markets' numbering and table (the areas were redrawn); the caller sets the bookkeeping arrays."""
        self.goods_markets = numbering
        self.goods_table = table
        self.rebind()

    def state(self) -> Dict[str, List[str]]:
        """What a save stores: every numbering as its ordered name list."""
        return {"goods": self.goods.state(), "trades": self.trades.state(), "areas": self.areas.state(),
                "kinds": self.kinds.state(), "goods_markets": self.goods_markets.state(),
                "labour_markets": self.labour_markets.state()}

    def load_state(self, state: Optional[Dict[str, List[str]]]) -> None:
        """Take the numberings a save stored (an empty table when none): the markets get their old numbers, blank, to be filled by
        the stores. The bookkeeping starts again."""
        state = state or {}
        self.goods = IdTable.from_state("good", state.get("goods", ()))
        self.trades = IdTable.from_state("trade", state.get("trades", ()))
        self.areas = IdTable.from_state("area", state.get("areas", ()))
        self.kinds = IdTable.from_state("quote kind", state.get("kinds", ()))
        self.goods_markets = IdTable.from_state("goods market", state.get("goods_markets", ()))
        self.labour_markets = IdTable.from_state("labour market", state.get("labour_markets", ()))
        self.goods_table = self._table_for(self.goods_markets, self.goods, GOODS_MARKETS, GoodsMarkets, _FLOAT_COLUMNS_OF_GOODS)
        self.labour_table = self._table_for(self.labour_markets, self.trades, LABOUR_MARKETS, LabourMarkets, ("wage",))
        self.next_order[:] = 0
        self.member_count[:] = 0
        self.rebind()

    def _table_for(self, numbering: IdTable, first_table: IdTable, spec, table_type, float_columns):
        """A blank table with a row per market of the numbering, `first` and `area` filled from the market names."""
        rows = len(numbering)
        table = spec.new_table(table_type, max(_FIRST_CAPACITY, rows), rows)
        blank_rows(table, 0, rows, float_columns)
        for row, name in enumerate(numbering.names):
            first, _separator, area = name.partition(KEY_SEPARATOR)
            table.first[row] = first_table.number(first)
            table.area[row] = self.areas.number(area)
        return table

    def blank_goods_table(self, numbering: IdTable):
        """A blank goods table with a row per market of `numbering` (a numbering not yet installed), the goods and areas in the
        market names numbered first."""
        parts = [name.partition(KEY_SEPARATOR) for name in numbering.names]
        self.goods.admit([part[0] for part in parts])
        self.areas.admit([part[2] for part in parts])
        return self._table_for(numbering, self.goods, GOODS_MARKETS, GoodsMarkets, _FLOAT_COLUMNS_OF_GOODS)

    @classmethod
    def from_state(cls, state: Optional[Dict[str, List[str]]]) -> "MarketTables":
        tables = cls()
        tables.load_state(state)
        return tables
