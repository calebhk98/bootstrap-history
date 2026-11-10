"""The year ledger's storage: its tables, their room, and the way a name becomes a number.

`LedgerTables` holds the agent figures, the eight pair tables, the market figures and the clearing rounds, and the counters that
keep entry order. It owns no numbering: agents, goods and purposes are the book's (`book.agent_number`, `good_number`,
`purposes`), goods markets, labour markets and trades are the market memory's (`MarketTables`). A game passes both
(`YearLedger(book=..., markets=...)`); a ledger built bare, as a test does, gets a book and market tables of its own.

Room is reserved here before a kernel runs, never inside one: `fit_agents` and `fit_markets` give a row to every number the
numberings have admitted, and `PairStore.reserve` leaves room for the rows a call can add."""
import numpy

from sim.book_index import EMPTY, FIRST_SHIFT, SECOND_SHIFT, KeyedRows
from sim.book_store import BookStore
from sim.compiled_tables.growth import reserve_rows
from sim.economy.market_tables import MarketTables
from sim.economy.year_ledger_batch import PendingNotes
from sim.economy.year_ledger_tables import (AGENT_FIGURES, CLEARING_ROUNDS, FIGURE_COUNT, GROWN, HOURS_HIRED, MARKET_FIGURE_COUNT,
                                            MARKET_FIGURES, PAIR_ROWS, RECEIVED, AgentFigures, ClearingRounds, MarketFigures,
                                            PairRows, PairTarget)

_NO_LINKS = numpy.zeros(0, dtype=numpy.int64)
_FIRST_ROOM = 64
# The pair tables, and for those whose agents own rows the agent figure that records the agent has some.
PAIR_FIGURES = {"received": RECEIVED, "grown": GROWN, "hours_hired": HOURS_HIRED, "sold": None, "output": None,
                "hours_hired_by_market": None, "imports_paid": None, "exports_received": None}


class PairStore:
    """One pair table with its hash index, and the count of rows the Python side has killed (a view caches by it)."""

    def __init__(self, tables: "LedgerTables", name: str) -> None:
        self.tables = tables
        self.name = name
        self.figure = PAIR_FIGURES[name]
        self.rows = KeyedRows(PAIR_ROWS, PairRows, _FIRST_ROOM)
        self.kills = 0
        self._lookup = {}          # packed key -> row for the rows below `_synced_rows`, for a reader that asks one key at a time
        self._synced_rows = 0

    def reserve(self, extra: int) -> None:
        """Room for `extra` more rows (the table and its index are replaced when it grows)."""
        self.rows.reserve(extra)

    def target(self) -> PairTarget:
        """What a pair kernel takes, as the tables are now (fetch it again after anything that may grow a table)."""
        figures = self.tables.figures
        chained = self.figure is not None
        if chained:
            firsts, lasts, orders = getattr(figures, "first_" + self.name), getattr(figures, "last_" + self.name), getattr(
                figures, "order_" + self.name)
        else:
            firsts = lasts = orders = _NO_LINKS
        return PairTarget(self.rows.table, self.rows.index, firsts, lasts, orders, self.tables.counters,
                          self.figure if chained else 0, chained)

    @property
    def row_count(self) -> int:
        return int(self.rows.table.row_count[0])

    def chain_rows(self, agent: int) -> list:
        """The agent's rows in a chained table, in the order they were made."""
        link = getattr(self.tables.figures, "first_" + self.name).item(agent)
        follow, found = self.rows.table.next_in_agent.item, []
        while link:
            found.append(link - 1)
            link = follow(link - 1)
        return found

    def forget_rows(self, rows) -> None:
        """Call before killing rows: the one-key lookup drops them and the views' caches see that rows were killed."""
        if rows:
            keys = self.rows.table.key
            for row in rows:
                self._lookup.pop(keys.item(row), None)
            self.kills += 1

    def row_of(self, agent: int, subkey: int, extra: int) -> int:
        """The live row for (agent, subkey, extra), or EMPTY: a Python dict kept up to date with the table (it takes the new rows
        on each ask; `kill_rows` removes the killed). A kernel asks the hash index."""
        table = self.rows.table
        count = int(table.row_count[0])
        if self._synced_rows < count:
            keys = table.key[self._synced_rows:count].tolist()
            self._lookup.update((key, row) for row, key in enumerate(keys, self._synced_rows) if key >= 0)
            self._synced_rows = count
        return self._lookup.get((agent << FIRST_SHIFT) | (subkey << SECOND_SHIFT) | extra, EMPTY)


class LedgerTables:
    def __init__(self, book=None, markets=None) -> None:
        self.book = book if book is not None else BookStore()
        self.markets = markets if markets is not None else MarketTables()
        self.figures = AGENT_FIGURES.new_table(AgentFigures, _FIRST_ROOM)
        self.counters = numpy.zeros(2 * FIGURE_COUNT, dtype=numpy.int64)
        self.pairs = {name: PairStore(self, name) for name in PAIR_FIGURES}
        self.market_figures = MARKET_FIGURES.new_table(MarketFigures, _FIRST_ROOM)
        self.market_counters = numpy.zeros(2 * MARKET_FIGURE_COUNT, dtype=numpy.int64)
        self.rounds = CLEARING_ROUNDS.new_table(ClearingRounds, _FIRST_ROOM)
        self.pending = PendingNotes()      # notes not yet in the tables (`year_ledger_batch.py`)

    def flush(self, kind=None) -> None:
        """Add the pending notes of one kind (all kinds when None) to the tables; call before reading or writing a table directly."""
        if kind is None:
            self.pending.flush_all(self)
        elif self.pending.counts[kind]:
            self.pending.flush(self, kind)

    # ---- rows for every number the numberings hold ----------------------------------------------------------------------

    def fit_agents(self) -> None:
        """A row in the agent figures for every agent the book has numbered (a new row holds nothing)."""
        wanted, used = len(self.book.agent_ids), int(self.figures.row_count[0])
        if wanted > used:
            self.figures = reserve_rows(self.figures, wanted - used)
            self.figures.row_count[0] = wanted

    def fit_markets(self) -> None:
        """A row in the market figures for every goods market the market memory has numbered."""
        wanted, used = len(self.markets.goods_markets), int(self.market_figures.row_count[0])
        if wanted > used:
            self.market_figures = reserve_rows(self.market_figures, wanted - used)
            self.market_figures.row_count[0] = wanted

    def reserve_rounds(self, extra: int) -> None:
        self.rounds = reserve_rows(self.rounds, extra)

    # ---- names to numbers ------------------------------------------------------------------------------------------------

    def agent_numbers(self, names) -> numpy.ndarray:
        """The book's number for each agent name, numbering (and giving a row to) any it has not met."""
        numbers = self.book.agent_ids.numbers
        try:
            found = [numbers[name] for name in names]
        except KeyError:
            found = [self.book.agent_number(name) for name in names]
        self.fit_agents()
        return numpy.array(found, dtype=numpy.int64)

    def agent_number(self, name: str) -> int:
        number = self.book.agent_number(name)
        if number >= int(self.figures.row_count[0]):
            self.fit_agents()
        return number

    def good_numbers(self, goods) -> numpy.ndarray:
        numbers = self.book.good_ids.numbers
        try:
            found = [numbers[good] for good in goods]
        except KeyError:
            found = [self.book.good_number(good) for good in goods]
        return numpy.array(found, dtype=numpy.int64)

    def purpose_code(self, text: str):
        """(template, reference) of a purpose text: the pair the book numbered it by when it posted it."""
        return self.book.purposes.encode(text)

    def market_number(self, good: str, area: str) -> int:
        """The goods market's number in the market memory, numbering it when new; it has a row in the market figures."""
        number = self.markets.goods_row_for_write(good + "|" + area)
        if number >= int(self.market_figures.row_count[0]):
            self.fit_markets()
        return number

    def labour_market_number(self, trade: str, area: str) -> int:
        return self.markets.labour_row_for_write(trade + "|" + area)

    def trade_number(self, trade: str) -> int:
        number = self.markets.trades.numbers.get(trade)
        return int(self.markets.trades.admit((trade,))[0]) if number is None else number
