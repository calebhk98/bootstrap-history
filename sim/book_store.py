"""The book's storage: the ids, the tables and the hash indexes (sim/book_tables.py says what each holds), and the ways to
admit a name and to read a cell. `Book` (sim/book.py) is this plus the rules.

Ids are `IdTable`s: a name's number is its place in the table, never reused, saved as the name list. A batch of new names is
numbered in sorted order (`admit`). A name is admitted before a posting that mentions it is planned, and a refused posting
leaves the number behind but not the agent: `known` is set only when a posting is written, and every read through the book's
methods goes by `known` (an agent that rename gave away is unknown again, and keeps its number if its name comes back).

Balances sit at row agent * stride + currency. Admitting a currency beyond the stride lays the table out again with a wider
stride; admitting an agent only adds rows."""
from typing import Dict, Iterable, List, Optional, Sequence

import numpy

from sim.book_index import FIRST_FIELD_BITS, FIRST_SHIFT, SECOND_FIELD_BITS, SECOND_SHIFT, THIRD_FIELD_BITS, KeyedRows
from sim.book_purposes import Purposes
from sim.book_single import SinglePostings
from sim.book_tables import (AGENTS, BALANCES, CURRENCIES, EDGE_GOODS, FREE, GOODS, PURPOSE_FLOWS, STOCKS, Agents, Balances,
                             BookTables, Currencies, EdgeGoods, Goods, GoodsTables, MoneyTables, PurposeFlows, Stocks)
from sim.book_types import EDGE_PREFIX, EXTERNAL_PREFIX, MINT_ID, AgentId, BookError, CurrencyId, GoodId, TileId
from sim.compiled_tables.growth import reserve_rows
from sim.compiled_tables.ids import IdTable

FIRST_STRIDE = 4


def kind_of(agent: AgentId) -> str:
    """The text of the agent id before its first colon: "producer" for "producer:flour@rome", "" for "founder"."""
    return agent.partition(":")[0] if ":" in agent else ""


class BookStore:
    def __init__(self):
        self.agent_ids = IdTable("agent")
        self.good_ids = IdTable("good")
        self.tile_ids = IdTable("tile")
        self.currency_ids = IdTable("currency")
        self.kind_ids = IdTable("kind", [""])
        self.purposes = Purposes()
        self.stride = FIRST_STRIDE
        self.agent_table = AGENTS.new_table(Agents, 64)
        self.balance_table = BALANCES.new_table(Balances, 64 * self.stride)
        self.currency_table = CURRENCIES.new_table(Currencies, self.stride)
        self.good_table = GOODS.new_table(Goods, 16)
        self.stock_rows = KeyedRows(STOCKS, Stocks, 256)
        self.flow_rows = KeyedRows(PURPOSE_FLOWS, PurposeFlows, 64)
        self.edge_goods_rows = KeyedRows(EDGE_GOODS, EdgeGoods, 16)
        self.scratch = None            # plans reused by one posting call after another (sim/book_post.py)
        self.settled_plans = None
        self.single_postings = SinglePostings()     # one-row posting tables reused by `transfer` and `move` (sim/book_single.py)

    # ---- admitting names -------------------------------------------------------------------------

    def agent_number(self, agent: AgentId) -> int:
        """The agent's number, admitted when new."""
        number = self.agent_ids.numbers.get(agent)
        if number is None:
            number = self._admit_agents([agent])[0]
        return number

    def agent_numbers_in_order(self, agents: Iterable[AgentId]) -> List[int]:
        """Each agent's number, as `agent_number` gives it name by name: the names new to the book are admitted one at a time in
        the order given (`_agent_numbers` admits a batch's new names sorted, which numbers them differently)."""
        given = list(agents)
        found = list(map(self.agent_ids.numbers.get, given))
        if None in found:
            for position, number in enumerate(found):
                if number is None:
                    found[position] = self.agent_number(given[position])
        return found

    def _admit_agents(self, agents: Iterable[AgentId]) -> List[int]:
        given = list(agents)
        self.agent_ids.admit(given)
        self._fit_agents()
        numbers = self.agent_ids.numbers
        return [numbers[agent] for agent in given]

    def _fit_agents(self) -> None:
        """Rows for every admitted agent, their flags set from the name, and balance cells for each."""
        wanted = len(self.agent_ids)
        old = int(self.agent_table.row_count[0])
        if wanted <= old:
            return
        if wanted >= 1 << FIRST_FIELD_BITS:
            raise BookError("the book cannot number more than %d agents" % (1 << FIRST_FIELD_BITS))
        self.agent_table = reserve_rows(self.agent_table, wanted - old)
        kinds = self.kind_ids
        for number in range(old, wanted):
            name = self.agent_ids.name(number)
            self.agent_table.is_edge[number] = 1 if name.startswith(EDGE_PREFIX) else 0
            self.agent_table.is_mint[number] = 1 if name == MINT_ID else 0
            self.agent_table.is_external[number] = 1 if name.startswith(EXTERNAL_PREFIX) else 0
            self.agent_table.kind[number] = kinds.admit([kind_of(name)])[0]
            self.agent_table.first_slot[number] = FREE
            self.agent_table.last_slot[number] = FREE
        self.agent_table.row_count[0] = wanted
        cells = wanted * self.stride
        self.balance_table = reserve_rows(self.balance_table, cells - int(self.balance_table.row_count[0]))
        self.balance_table.row_count[0] = cells

    def good_number(self, good: GoodId) -> int:
        number = self.good_ids.find(good)
        if number is None:
            number = self._admit_goods([good])[0]
        return number

    def _admit_goods(self, goods: Iterable[GoodId]) -> List[int]:
        given = list(goods)
        numbers = self.good_ids.numbers
        found = [numbers.get(good) for good in given]
        if None not in found:
            return found
        self.good_ids.admit(given)
        self._fit_goods()
        return [numbers[good] for good in given]

    def _fit_goods(self) -> None:
        """A row in the goods table for every admitted good."""
        wanted, old = len(self.good_ids), int(self.good_table.row_count[0])
        if wanted >= 1 << SECOND_FIELD_BITS:
            raise BookError("the book cannot number more than %d goods" % (1 << SECOND_FIELD_BITS))
        if wanted > old:
            self.good_table = reserve_rows(self.good_table, wanted - old)
            self.good_table.row_count[0] = wanted

    def tile_number(self, tile: TileId) -> int:
        number = self.tile_ids.find(tile)
        if number is None:
            number = self._admit_tiles([tile])[0]
        return number

    def _admit_tiles(self, tiles: Iterable[TileId]) -> List[int]:
        given = list(tiles)
        numbers = self.tile_ids.numbers
        found = [numbers.get(tile) for tile in given]
        if None not in found:
            return found
        self.tile_ids.admit(given)
        if len(self.tile_ids) >= 1 << THIRD_FIELD_BITS:
            raise BookError("the book cannot number more than %d tiles" % (1 << THIRD_FIELD_BITS))
        return [numbers[tile] for tile in given]

    def currency_number(self, currency: CurrencyId) -> int:
        number = self.currency_ids.find(currency)
        if number is None:
            number = self._admit_currencies([currency])[0]
        return number

    def _admit_currencies(self, currencies: Iterable[CurrencyId]) -> List[int]:
        given = list(currencies)
        numbers = self.currency_ids.numbers
        found = [numbers.get(currency) for currency in given]
        if None not in found:
            return found
        self.currency_ids.admit(given)
        self._fit_currencies()
        return [numbers[currency] for currency in given]

    def _fit_currencies(self) -> None:
        """A row in the currencies table, and room in each agent's balance cells, for every admitted currency."""
        wanted = len(self.currency_ids)
        if wanted > self.stride:
            self._widen_stride(max(2 * self.stride, wanted))
        old = int(self.currency_table.row_count[0])
        if wanted > old:
            self.currency_table = reserve_rows(self.currency_table, wanted - old)
            self.currency_table.row_count[0] = wanted

    def _widen_stride(self, stride: int) -> None:
        """Lay the balance table out again with more room per agent for currencies."""
        agents, old = int(self.agent_table.row_count[0]), self.stride
        capacity = max(int(self.balance_table.capacity[0]) // old, agents) * stride
        wide = BALANCES.new_table(Balances, capacity, agents * stride)
        for column in BALANCES.columns:
            source = getattr(self.balance_table, column.name)[:agents * old].reshape(agents, old)
            getattr(wide, column.name)[:agents * stride].reshape(agents, stride)[:, :old] = source
        self.balance_table, self.stride = wide, stride

    # ---- the numbering, saved and restored ------------------------------------------------------

    def numbering_state(self) -> dict:
        """The ids as ordered name lists: what a save stores so a loaded book numbers as the live one did."""
        return {"agents": self.agent_ids.state(), "goods": self.good_ids.state(), "tiles": self.tile_ids.state(),
                "currencies": self.currency_ids.state(), "kinds": self.kind_ids.state(), "purposes": self.purposes.state()}

    def adopt_numbering(self, state: dict) -> None:
        """Number an empty book as the saved state says (names that no cell holds yet stay unknown)."""
        self.agent_ids = IdTable.from_state("agent", state["agents"])
        self.good_ids = IdTable.from_state("good", state["goods"])
        self.tile_ids = IdTable.from_state("tile", state["tiles"])
        self.currency_ids = IdTable.from_state("currency", state["currencies"])
        self.kind_ids = IdTable.from_state("kind", state["kinds"])
        self.purposes = Purposes.from_state(state["purposes"])
        self.agent_table = AGENTS.new_table(Agents, max(64, len(self.agent_ids)))
        self.balance_table = BALANCES.new_table(Balances, max(64, len(self.agent_ids)) * self.stride)
        self.good_table = GOODS.new_table(Goods, max(16, len(self.good_ids)))
        self.currency_table = CURRENCIES.new_table(Currencies, max(self.stride, len(self.currency_ids)))
        self._fit_agents()
        self._fit_goods()
        self._fit_currencies()

    # ---- the tables as a kernel takes them -------------------------------------------------------

    def money_tables(self) -> MoneyTables:
        """The tables a money posting reads and writes, as of now (growing a table makes a new one)."""
        return MoneyTables(self.agent_table, self.balance_table, self.stride, self.currency_table)

    def goods_tables(self) -> GoodsTables:
        """The tables a goods posting reads and writes, and the hash indexes over the keyed ones."""
        return GoodsTables(self.agent_table, self.good_table, self.stock_rows.table, self.stock_rows.index, self.flow_rows.table,
                           self.flow_rows.index, self.edge_goods_rows.table, self.edge_goods_rows.index)

    def tables(self) -> BookTables:
        return BookTables(self.money_tables(), self.goods_tables())

    # ---- single cells ----------------------------------------------------------------------------

    def _cell(self, agent: AgentId, currency: CurrencyId) -> Optional[int]:
        """The balance row for the pair, or None when either has never been admitted."""
        number, currency_number = self.agent_ids.find(agent), self.currency_ids.find(currency)
        if number is None or currency_number is None:
            return None
        return number * self.stride + currency_number

    def _slot_key(self, agent: AgentId, good: GoodId, tile: TileId) -> Optional[int]:
        """The packed stock key, or None when the agent, good or tile has never been admitted."""
        number, good_number, tile_number = self.agent_ids.find(agent), self.good_ids.find(good), self.tile_ids.find(tile)
        if number is None or good_number is None or tile_number is None:
            return None
        return (number << FIRST_SHIFT) | (good_number << SECOND_SHIFT) | tile_number

    def slot_for(self, agent: AgentId, good: GoodId, tile: TileId) -> int:
        """The stock slot for the cell, or -1 when nothing was ever held there."""
        key = self._slot_key(agent, good, tile)
        return -1 if key is None else self.stock_rows.find(key)

    def known_agent_numbers(self) -> numpy.ndarray:
        """The numbers of the agents the book knows, ascending."""
        return numpy.flatnonzero(self.agent_table.known[:int(self.agent_table.row_count[0])])

    def names_of(self, numbers: Sequence[int]) -> List[AgentId]:
        name = self.agent_ids.name
        return [name(number) for number in numbers]

    def by_name(self) -> Dict[AgentId, int]:
        """Every known agent's number by name."""
        name = self.agent_ids.name
        return {name(number): number for number in self.known_agent_numbers().tolist()}
