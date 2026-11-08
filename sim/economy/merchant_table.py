"""The merchants' per-merchant state as columns: one row per merchant of a record, shared by every kernel that works over merchants.

A `Merchant` (merchants.py) is a handle on a row: its capital base, its expected prices and volumes, the hauls still on the
road and the prices news has not yet reached it with are read from and written to this table, so a phase that closes or
learns for every merchant is one kernel over the table and builds no per-merchant object.

Columns (row = a merchant, in the order the merchants were put in the record; `rank_order()` gives them by agent id):
- `capital_base`      float, currency units: capital staked in trade; profit is wealth above it.
- `prices`, `volumes` float matrices [merchant row, goods-market row], the record's goods-market numbering (`tables.goods_markets`);
                      NaN where the merchant has no figure. `RowFigures` is the dict-like view of one row.
- shipments (ragged, rows in no fixed order, a merchant's own rows in the order they were added): `transit_owner` (merchant row),
                      `transit_good` (`goods` number), `transit_quantity` (units), `transit_tile` (`tiles` number, where the goods wait
                      in the transit account), `transit_years` (year-ends before they reach it).
- price history (ragged, sorted by key): `history_key` = merchant row * HISTORY_STRIDE + goods-market row, `history_starts`
                      (offsets into `history_price`), `history_price` (prices of a distant market that news has not yet reached,
                      oldest first).
`goods` and `tiles` number the names the shipments hold; numbers mean nothing outside this table."""
from typing import Dict, Iterable, List, Optional, Tuple

import numpy

from sim.compiled_tables.ids import IdTable

from .merchant_figures import MarketFigures, market_name

HISTORY_STRIDE = 1 << 32          # a history key packs (merchant row, market row)
FIRST_ROWS = 8
FIRST_COLUMNS = 64


class RowFigures(MarketFigures):
    """One row of the table's price or volume matrix, as the dict-like `MarketFigures` the merchant's readers use."""

    def __init__(self, store: "MerchantTable", matrix_name: str, row: int) -> None:    # pylint: disable=super-init-not-called
        self._store = store
        self._matrix_name = matrix_name
        self._row_number = row
        self._tables = store.tables
        self._pending = None

    @property
    def _numbering(self):      # type: ignore[override]
        return self._store.numbering

    def _chosen(self):
        return self._tables

    def _current(self) -> numpy.ndarray:
        self._store.fit_columns()
        return getattr(self._store, self._matrix_name)[self._row_number]

    def follow(self, old_to_new, new_rows, old_rows) -> None:
        """Carry every merchant's figures over to the new numbering (once, whichever merchant is asked first)."""
        self._store.follow(old_to_new, new_rows, old_rows)

    def bind(self, tables) -> None:
        if tables is not self._tables:
            raise ValueError("a figure row of a merchant table cannot be indexed by another numbering")

    def replace_all(self, items) -> None:
        held = [(key, figure) for key, figure in (items.items() if hasattr(items, "items") else items)
                if figure is not None]
        self._current()[:] = numpy.nan
        self.update(held)


class MerchantTable:
    """See the module docstring. One per record, found by `MerchantTable.of(record.memory.tables)`."""

    def __init__(self, tables) -> None:
        self.tables = tables
        self.numbering = tables.goods_markets
        self.agents: List[str] = []
        self.row_of: Dict[str, int] = {}
        self.homes: List[str] = []         # the tile each merchant keeps its purse on
        self.owners: List[str] = []        # who receives each merchant's profit
        self.capital_base = numpy.zeros(FIRST_ROWS)
        self.prices = numpy.full((FIRST_ROWS, FIRST_COLUMNS), numpy.nan)
        self.volumes = numpy.full((FIRST_ROWS, FIRST_COLUMNS), numpy.nan)
        self.goods = IdTable("good")
        self.tiles = IdTable("tile")
        self.transit_count = 0
        self.transit_owner = numpy.zeros(FIRST_ROWS, numpy.int64)
        self.transit_good = numpy.zeros(FIRST_ROWS, numpy.int64)
        self.transit_quantity = numpy.zeros(FIRST_ROWS)
        self.transit_tile = numpy.zeros(FIRST_ROWS, numpy.int64)
        self.transit_years = numpy.zeros(FIRST_ROWS, numpy.int64)
        self.history_key = numpy.zeros(0, numpy.int64)
        self.history_starts = numpy.zeros(1, numpy.int64)
        self.history_price = numpy.zeros(0)
        self._rank_cache: Optional[Tuple[int, numpy.ndarray]] = None
        self._pending_history: Dict[int, Dict[Tuple[str, str], List[float]]] = {}      # histories held by name while the areas are redrawn

    @classmethod
    def of(cls, tables) -> "MerchantTable":
        """The merchant table of this goods-market numbering, made when first asked for."""
        found = tables.__dict__.get("merchant_table")
        if found is None:
            found = tables.merchant_table = cls(tables)
        return found

    # ---- rows ---------------------------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.agents)

    def add(self, agent_id: str) -> int:
        """The row of this merchant, a new one (blank) when it has none."""
        row = self.row_of.get(agent_id)
        if row is not None:
            return row
        row = len(self.agents)
        if row >= len(self.capital_base):
            size = 2 * len(self.capital_base)
            self.capital_base = _grown(self.capital_base, size)
            self.prices = _grown(self.prices, size)
            self.volumes = _grown(self.volumes, size)
        self.agents.append(agent_id)
        self.homes.append("")
        self.owners.append("")
        self.row_of[agent_id] = row
        self.capital_base[row] = 0.0
        self.prices[row] = numpy.nan
        self.volumes[row] = numpy.nan
        self._rank_cache = None
        return row

    def rank_order(self) -> numpy.ndarray:
        """The merchant rows by agent id (the order every year's rotation and sums use)."""
        if self._rank_cache is None or self._rank_cache[0] != len(self.agents):
            order = numpy.array(sorted(range(len(self.agents)), key=self.agents.__getitem__), numpy.int64)
            self._rank_cache = (len(self.agents), order)
        return self._rank_cache[1]

    def rows_of(self, agents: Iterable[str]) -> numpy.ndarray:
        return numpy.array([self.row_of[agent] for agent in agents], numpy.int64)

    # ---- figures ------------------------------------------------------------------------------------

    def fit_columns(self) -> None:
        """Grow the matrices to the length of the numbering (NaN for markets numbered since); a renumbering that was not followed raises."""
        if self.tables.goods_markets is not self.numbering:
            raise RuntimeError("the goods markets were renumbered and this merchant's figures were not carried over (follow)")
        size = len(self.numbering)
        if self.prices.shape[1] < size:
            width = max(size, 2 * self.prices.shape[1])
            self.prices = _grown_columns(self.prices, width)
            self.volumes = _grown_columns(self.volumes, width)

    def follow(self, old_to_new: numpy.ndarray, new_rows: numpy.ndarray, old_rows: numpy.ndarray) -> None:
        """Carry the figures of every merchant over to the numbering that replaced the old one (`MarketFigures.follow`, for all rows)."""
        if self.numbering is self.tables.goods_markets:
            return
        old_numbering = self.numbering
        for name in ("prices", "volumes"):
            old = getattr(self, name)
            width = max(FIRST_COLUMNS, len(self.tables.goods_markets))
            fresh = numpy.full((old.shape[0], width), numpy.nan)
            shared = min(len(old_to_new), old.shape[1])
            survives = old_to_new[:shared] >= 0
            fresh[:, old_to_new[:shared][survives]] = old[:, :shared][:, survives]
            copies = old_rows >= 0
            old_padded = numpy.full((old.shape[0], len(old_to_new)), numpy.nan)
            old_padded[:, :shared] = old[:, :shared]
            fresh[:, new_rows[copies]] = old_padded[:, old_rows[copies]]
            setattr(self, name, fresh)
        self._pending_history = self._history_by_name(old_numbering)      # re-keyed by each merchant (`set_history`) over the new areas
        self.history_key, self.history_starts, self.history_price = _pack_history({})
        self.numbering = self.tables.goods_markets

    def gather(self, matrix_name: str, rows: numpy.ndarray, market_rows: numpy.ndarray) -> numpy.ndarray:
        """The figures of the merchants at `rows` in the markets at `market_rows` (-1: no such market, NaN), one row per merchant."""
        self.fit_columns()
        found = getattr(self, matrix_name)[numpy.ix_(rows, numpy.where(market_rows >= 0, market_rows, 0))]
        found[:, market_rows < 0] = numpy.nan
        return found

    def figures(self, matrix_name: str, row: int) -> RowFigures:
        return RowFigures(self, matrix_name, row)

    # ---- shipments ----------------------------------------------------------------------------------

    def shipments_of(self, row: int) -> List[Tuple[str, float, str, int]]:
        """(good, quantity, destination tile, years left) of the merchant's hauls on the road, in the order they were added."""
        places = numpy.flatnonzero(self.transit_owner[:self.transit_count] == row)
        goods, tiles = self.goods.name_list, self.tiles.name_list
        return [(goods[self.transit_good[place]], float(self.transit_quantity[place]), tiles[self.transit_tile[place]],
                 int(self.transit_years[place])) for place in places.tolist()]

    def set_shipments(self, row: int, shipments: Iterable[Tuple[str, float, str, int]]) -> None:
        """Replace the merchant's hauls on the road."""
        keep = self.transit_owner[:self.transit_count] != row
        self._compact(keep)
        for good, quantity, tile, years in shipments:
            self.add_shipment(row, good, quantity, tile, years)

    def add_shipment(self, row: int, good: str, quantity: float, tile: str, years: int) -> None:
        if self.transit_count >= len(self.transit_owner):
            size = 2 * len(self.transit_owner)
            for name in ("transit_owner", "transit_good", "transit_quantity", "transit_tile", "transit_years"):
                setattr(self, name, _grown(getattr(self, name), size))
        good_number, tile_number = int(self.goods.admit([good])[0]), int(self.tiles.admit([tile])[0])
        place = self.transit_count
        self.transit_owner[place], self.transit_good[place] = row, good_number
        self.transit_quantity[place], self.transit_tile[place], self.transit_years[place] = quantity, tile_number, years
        self.transit_count += 1

    def _compact(self, keep: numpy.ndarray) -> None:
        kept = int(keep.sum())
        for name in ("transit_owner", "transit_good", "transit_quantity", "transit_tile", "transit_years"):
            column = getattr(self, name)
            column[:kept] = column[:self.transit_count][keep]
        self.transit_count = kept

    # ---- price history ------------------------------------------------------------------------------

    def history_of(self, row: int) -> Dict[Tuple[str, str], List[float]]:
        """{(good, area id): prices, oldest first} of the merchant."""
        if row in self._pending_history:
            return {key: list(prices) for key, prices in self._pending_history[row].items()}
        return self._history_by_name(self.numbering, row).get(row, {})

    def _history_by_name(self, numbering, only_row: Optional[int] = None) -> Dict[int, Dict[Tuple[str, str], List[float]]]:
        names = numbering.name_list
        found: Dict[int, Dict[Tuple[str, str], List[float]]] = {}
        for place, key in enumerate(self.history_key.tolist()):
            owner, market = key // HISTORY_STRIDE, key % HISTORY_STRIDE
            if only_row is None or owner == only_row:
                found.setdefault(owner, {})[MarketFigures.key_of_name(names[market])] = \
                    self.history_price[self.history_starts[place]:self.history_starts[place + 1]].tolist()
        return found

    def set_history(self, row: int, histories: Dict[Tuple[str, str], List[float]]) -> None:
        """Replace the merchant's price history (a market the numbering has not yet numbered is numbered)."""
        self._pending_history.pop(row, None)
        self.tables.admit_goods_markets([market_name(key) for key in histories])
        self.fit_columns()
        merged = self._history_dict()
        for key in [key for key in merged if key[0] == row]:
            del merged[key]
        for key, prices in histories.items():
            merged[(row, self.tables.goods_numbers[market_name(key)])] = list(prices)
        self.history_key, self.history_starts, self.history_price = _pack_history(merged)

    def flush_pending_history(self) -> None:
        """Index the histories held by name (none unless the areas were just redrawn and a merchant was not yet re-keyed)."""
        if not self._pending_history or self.numbering is not self.tables.goods_markets:
            return
        held, self._pending_history = self._pending_history, {}
        self.tables.admit_goods_markets([market_name(key) for each in held.values() for key in each])
        merged = self._history_dict()
        for row, each in held.items():
            for key, prices in each.items():
                merged[(row, self.tables.goods_numbers[market_name(key)])] = list(prices)
        self.history_key, self.history_starts, self.history_price = _pack_history(merged)

    def _history_dict(self) -> Dict[Tuple[int, int], List[float]]:
        return {(int(key // HISTORY_STRIDE), int(key % HISTORY_STRIDE)):
                self.history_price[self.history_starts[place]:self.history_starts[place + 1]].tolist()
                for place, key in enumerate(self.history_key.tolist())}


def _pack_history(histories: Dict[Tuple[int, int], List[float]]):
    keys = sorted(histories)
    starts = numpy.zeros(len(keys) + 1, numpy.int64)
    for place, key in enumerate(keys):
        starts[place + 1] = starts[place] + len(histories[key])
    prices = numpy.array([price for key in keys for price in histories[key]], numpy.float64)
    return numpy.array([owner * HISTORY_STRIDE + market for owner, market in keys], numpy.int64), starts, prices


def _grown(column: numpy.ndarray, size: int) -> numpy.ndarray:
    fresh = numpy.full((size,) + column.shape[1:], numpy.nan) if column.dtype.kind == "f" and column.ndim == 2 else numpy.zeros((size,) + column.shape[1:], column.dtype)
    fresh[:len(column)] = column
    return fresh


def _grown_columns(matrix: numpy.ndarray, width: int) -> numpy.ndarray:
    fresh = numpy.full((matrix.shape[0], width), numpy.nan)
    fresh[:, :matrix.shape[1]] = matrix
    return fresh


def adopt(merchant, tables) -> None:
    """Move the merchant's state into the table of this numbering (its own, when it is in another) and index its figures by it."""
    store = MerchantTable.of(tables)
    if merchant.__dict__.get("_store") is store:
        return
    state = merchant.state_for_table()
    row = store.add(merchant.agent_id)
    merchant.__dict__["_store"] = store
    merchant.__dict__["_row"] = row
    merchant.__dict__["expected_prices"] = store.figures("prices", row)
    merchant.__dict__["expected_volumes"] = store.figures("volumes", row)
    store.homes[row], store.owners[row] = merchant.home_tile, merchant.owner
    store.capital_base[row] = state["capital_base"]
    for name, names_figures in (("expected_prices", state["expected_prices"]), ("expected_volumes", state["expected_volumes"])):
        figures = merchant.__dict__[name]
        figures.replace_all(zip(map(MarketFigures.key_of_name, names_figures[0]), names_figures[1]))
    store.set_shipments(row, state["in_transit"])
    store.set_history(row, state["price_history"])
