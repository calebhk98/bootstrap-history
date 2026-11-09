"""The ledger's pair tables as dicts (see year_ledger_views.py for what every view promises).

    PairView    (agent, sub...) -> float, or (hours, money) for hours_hired_by_market      sold, output, imports_paid, exports_received,
                                                                                            hours_hired_by_market
    NestedView  agent -> InnerView, agents in the order they first had an entry            received, grown, hours_hired
    InnerView   sub -> float: one agent's rows, live (assigning to it changes the table)"""
from typing import Iterator, List, Optional, Tuple

import numpy

from sim.book_index import EMPTY
from sim.economy.year_ledger_plain import plain_by_agent
from sim.economy.year_ledger_kernels import add_pair, clear_agent_rows, kill_row, remove_from_figure, set_pair, touch
from sim.economy.year_ledger_store import LedgerTables, PairStore
from sim.economy.year_ledger_tables import PAIR_KIND, MEMBERS, NEXT_ENTRY
from sim.economy.year_ledger_views import Show, flushed, in_entry_order


def put_pair(store: PairStore, agent: int, sub: Tuple[int, int], value, add: bool = False) -> None:
    """Set (or add to) the figure of the row for (agent, sub); a pair value is (amount, second amount)."""
    store.reserve(1)
    amount, second = value if isinstance(value, tuple) else (value, 0.0)
    (add_pair if add else set_pair)(store.target(), agent, sub[0], sub[1], float(amount), float(second))


class PairView(Show):
    """Rows nobody reads by agent: one entry per row, in the order the rows were made."""

    def __init__(self, tables: LedgerTables, store: PairStore, sub) -> None:
        self._tables = tables
        self._store = store
        self._kind = PAIR_KIND[store.name]
        self._sub = sub
        self._two_figures = store.name == "hours_hired_by_market"
        self._cache = None

    @staticmethod
    def _split(key):
        """(agent name, the rest of the key) of a key tuple; the rest is one thing, or a tuple for a labour market."""
        return key[0], (key[1] if len(key) == 2 else key[1:])

    def _row_of(self, key) -> int:
        agent = self._tables.book.agent_ids.numbers.get(key[0])
        sub = self._sub.find(key[1] if len(key) == 2 else key[1:])
        if agent is None or sub is None:
            return EMPTY
        return self._store.row_of(agent, sub[0], sub[1])

    def _value(self, row: int):
        rows = self._store.rows.table
        return (rows.amount.item(row), rows.second_amount.item(row)) if self._two_figures else rows.amount.item(row)

    def _rows(self) -> Tuple[numpy.ndarray, list]:
        """(the live rows, their keys), kept until a row is made or killed."""
        rows = self._store.rows.table
        stamp = (self._store.row_count, self._store.kills)
        if self._cache is None or self._cache[0] is not rows or self._cache[1] != stamp:
            live = numpy.flatnonzero(rows.live[:stamp[0]])
            names = self._tables.book.agent_ids.name_list
            subs = self._sub.names(rows.subkey[live].tolist(), rows.extra[live].tolist())
            keys = [(names[agent],) + (sub if isinstance(sub, tuple) else (sub,)) for agent, sub in zip(rows.agent[live].tolist(), subs)]
            self._cache = (rows, stamp, live, keys)
        return self._cache[2], self._cache[3]

    @flushed
    def __len__(self) -> int:
        return len(self._rows()[0])

    @flushed
    def __iter__(self) -> Iterator:
        return iter(self._rows()[1])

    @flushed
    def keys(self) -> List:
        return list(self._rows()[1])

    @flushed
    def items(self) -> List[tuple]:
        live, keys = self._rows()
        table = self._store.rows.table
        if self._two_figures:
            return list(zip(keys, zip(table.amount[live].tolist(), table.second_amount[live].tolist())))
        return list(zip(keys, table.amount[live].tolist()))

    @flushed
    def values(self) -> list:
        return [value for _key, value in self.items()]

    @flushed
    def __contains__(self, key) -> bool:
        return self._row_of(key) != EMPTY

    @flushed
    def __getitem__(self, key):
        row = self._row_of(key)
        if row == EMPTY:
            raise KeyError(key)
        return self._value(row)

    @flushed
    def get(self, key, default=None):
        row = self._row_of(key)
        return default if row == EMPTY else self._value(row)

    @flushed
    def __setitem__(self, key, value) -> None:
        agent = self._tables.agent_number(key[0])
        put_pair(self._store, agent, self._sub.make(self._split(key)[1]), value)

    @flushed
    def __delitem__(self, key) -> None:
        row = self._row_of(key)
        if row == EMPTY:
            raise KeyError(key)
        self._store.forget_rows([row])
        kill_row(self._store.target(), row)


class InnerView(Show):
    """One agent's `sub -> float` dict inside a NestedView: the rows on the agent's chain, live."""

    def __init__(self, nested: "NestedView", agent: int) -> None:
        self._nested = nested
        self._tables = nested._tables
        self._kind = nested._kind
        self._agent = agent

    def _chain(self) -> List[int]:
        return self._nested._store.chain_rows(self._agent)

    def _row_of(self, sub) -> int:
        found = self._nested._sub.find(sub)
        return EMPTY if found is None else self._nested._store.row_of(self._agent, found[0], found[1])

    @flushed
    def __len__(self) -> int:
        return len(self._chain())

    @flushed
    def __iter__(self) -> Iterator:
        return iter(self.keys())

    @flushed
    def items(self) -> List[tuple]:
        table, name = self._nested._store.rows.table, self._nested._sub.name
        return [(name(table.subkey.item(row), table.extra.item(row)), table.amount.item(row)) for row in self._chain()]

    @flushed
    def keys(self) -> List:
        table, name = self._nested._store.rows.table, self._nested._sub.name
        return [name(table.subkey.item(row), table.extra.item(row)) for row in self._chain()]

    @flushed
    def values(self) -> List[float]:
        table = self._nested._store.rows.table
        return [table.amount.item(row) for row in self._chain()]

    @flushed
    def __contains__(self, sub) -> bool:
        return self._row_of(sub) != EMPTY

    @flushed
    def __getitem__(self, sub) -> float:
        row = self._row_of(sub)
        if row == EMPTY:
            raise KeyError(sub)
        return self._nested._store.rows.table.amount.item(row)

    @flushed
    def get(self, sub, default=None):
        row = self._row_of(sub)
        return default if row == EMPTY else self._nested._store.rows.table.amount.item(row)

    @flushed
    def __setitem__(self, sub, value: float) -> None:
        put_pair(self._nested._store, self._agent, self._nested._sub.make(sub), float(value))

    @flushed
    def __delitem__(self, sub) -> None:
        if self._row_of(sub) == EMPTY:
            raise KeyError(sub)
        self._nested._replace(self._agent, [(key, value) for key, value in self.items() if key != sub])


class NestedView(Show):
    """Agent name -> that agent's `sub -> float` dict, agents in the order they first had an entry."""

    def __init__(self, tables: LedgerTables, store: PairStore, sub) -> None:
        self._tables = tables
        self._store = store
        self._kind = PAIR_KIND[store.name]
        self._sub = sub
        self._order = "order_" + store.name
        self._cache = None

    def _members(self) -> Tuple[numpy.ndarray, list]:
        figures, counters, figure = self._tables.figures, self._tables.counters, self._store.figure
        stamp = (int(counters[2 * figure + NEXT_ENTRY]), int(counters[2 * figure + MEMBERS]))
        if self._cache is None or self._cache[0] is not figures or self._cache[1] != stamp:
            rows = in_entry_order(getattr(figures, self._order), int(figures.row_count[0]))
            names = self._tables.book.agent_ids.name_list
            self._cache = (figures, stamp, rows, [names[row] for row in rows.tolist()])
        return self._cache[2], self._cache[3]

    def _agent_of(self, name) -> Optional[int]:
        agent = self._tables.book.agent_ids.numbers.get(name)
        if agent is None:
            return None
        try:
            return agent if getattr(self._tables.figures, self._order).item(agent) else None
        except IndexError:
            return None

    @flushed
    def __len__(self) -> int:
        return int(self._tables.counters[2 * self._store.figure + MEMBERS])

    @flushed
    def __iter__(self) -> Iterator:
        return iter(self._members()[1])

    @flushed
    def keys(self) -> List:
        return list(self._members()[1])

    @flushed
    def items(self) -> List[tuple]:
        rows, names = self._members()
        return [(name, InnerView(self, agent)) for name, agent in zip(names, rows.tolist())]

    @flushed
    def values(self) -> List[InnerView]:
        return [view for _name, view in self.items()]

    @flushed
    def as_plain(self) -> dict:
        """Every agent's rows as plain `sub -> amount` dicts, agents in entry order and each agent's rows in the order they were made:
        what `{name: dict(inner.items()) for name, inner in self.items()}` gives, read from the table in one pass. Not live."""
        members, names = self._members()
        table = self._store.rows.table
        live = numpy.flatnonzero(table.live[:self._store.row_count])
        return plain_by_agent(members, names, table.agent[live], table.subkey[live], table.extra[live], table.amount[live], self._sub.names)

    @flushed
    def __contains__(self, name) -> bool:
        return self._agent_of(name) is not None

    @flushed
    def __getitem__(self, name) -> InnerView:
        agent = self._agent_of(name)
        if agent is None:
            raise KeyError(name)
        return InnerView(self, agent)

    @flushed
    def get(self, name, default=None):
        agent = self._agent_of(name)
        return default if agent is None else InnerView(self, agent)

    def _replace(self, agent: int, entries) -> None:
        """Give the agent exactly these (sub, amount) entries, in this order, keeping its place among the agents."""
        touch(getattr(self._tables.figures, self._order), self._tables.counters, self._store.figure, agent)
        self._store.forget_rows(self._store.chain_rows(agent))
        clear_agent_rows(self._store.target(), agent)
        for sub, amount in entries:
            put_pair(self._store, agent, self._sub.make(sub), float(amount))

    @flushed
    def __setitem__(self, name, entries) -> None:
        self._replace(self._tables.agent_number(name), list(dict(entries).items()))

    @flushed
    def setdefault(self, name, default=None) -> InnerView:
        """The agent's live dict; made empty (or as `default` says) when the agent has none yet."""
        if self._agent_of(name) is None:
            self[name] = default if default is not None else {}
        return self[name]

    @flushed
    def __delitem__(self, name) -> None:
        agent = self._agent_of(name)
        if agent is None:
            raise KeyError(name)
        self._store.forget_rows(self._store.chain_rows(agent))
        clear_agent_rows(self._store.target(), agent)
        remove_from_figure(getattr(self._tables.figures, self._order), self._tables.counters, self._store.figure, agent)
