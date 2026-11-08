"""The book's reads, by name: what an agent holds, totals, this year's flows, and the conservation check.

A mixin of `Book` (sim/book.py), which owns the layout (sim/book_store.py). Each read turns names into ids, reads the tables
and turns the answer back into names; a name the book never saw reads as nothing held. A converter holding ids uses the
kernels in sim/book_read_kernels.py instead."""
import math
from typing import Dict, List

import numpy

from sim.book_index import EMPTY, FIRST_SHIFT, SECOND_SHIFT, index_find
from sim.book_read_kernels import counted_stocks, currency_values, good_quantities, holder_columns
from sim.book_types import AgentId, ConservationReport, CurrencyId, GoodId, TileId, _share


class BookReads:
    # ---- one cell ----------------------------------------------------------------------------------

    def balance(self, agent: AgentId, currency: CurrencyId) -> float:
        number = self.agent_ids.numbers.get(agent)
        currency_number = self.currency_ids.numbers.get(currency)
        if number is None or currency_number is None:
            return 0.0
        return self.balance_table.amount.item(number * self.stride + currency_number)

    def stock(self, agent: AgentId, good: GoodId, tile: TileId) -> float:
        number, good_number, tile_number = (self.agent_ids.numbers.get(agent), self.good_ids.numbers.get(good),
                                            self.tile_ids.numbers.get(tile))
        if number is None or good_number is None or tile_number is None:
            return 0.0
        table = self.stock_rows.table
        slot = index_find(table.key, self.stock_rows.index, (number << FIRST_SHIFT) | (good_number << SECOND_SHIFT) | tile_number)
        return 0.0 if slot == EMPTY else table.quantity.item(slot)

    def knows(self, agent: AgentId) -> bool:
        """Whether the agent has ever held or paid anything in this book."""
        number = self.agent_ids.numbers.get(agent)
        return number is not None and self.agent_table.known.item(number) != 0

    # ---- one agent -----------------------------------------------------------------------------------

    def holdings(self, agent: AgentId) -> dict:
        number = self.agent_ids.numbers.get(agent)
        money = {}
        if number is not None and self.agent_table.known.item(number):
            for currency in sorted(self.currency_ids.names):
                cell = number * self.stride + self.currency_ids.find(currency)
                value = self.balance_table.amount.item(cell)
                if self.balance_table.seen.item(cell) and value != 0.0:
                    money[currency] = value
        return {"money": money, "goods": self.goods_held(agent)}

    def goods_of(self, agent: AgentId) -> Dict[GoodId, Dict[TileId, float]]:
        """What the agent holds, good to tile to quantity: a copy, in no stated order, and it may hold zeros.
        A caller that adds quantities sums them exactly."""
        number = self.agent_ids.numbers.get(agent)
        if number is None:
            return {}
        first = self.agent_table.first_slot.item(number)
        if first == -1:
            return {}
        table = self.stock_rows.table
        goods, tiles, quantities = holder_columns(first, table.next_in_agent, table.good, table.tile, table.quantity)
        good_names, tile_names = self.good_ids.name_list, self.tile_ids.name_list
        held: Dict[GoodId, Dict[TileId, float]] = {}
        for good, tile, quantity in zip(goods.tolist(), tiles.tolist(), quantities.tolist()):
            by_tile = held.get(good_names[good])
            if by_tile is None:
                by_tile = held[good_names[good]] = {}
            by_tile[tile_names[tile]] = quantity
        return held

    def goods_held(self, agent: AgentId) -> Dict[GoodId, Dict[str, float]]:
        """What the agent holds of each good, by tile: goods and tiles in name order, nothing at zero."""
        goods = {}
        for good, by_tile in sorted(self.goods_of(agent).items()):
            tiles = {tile: value for tile, value in sorted(by_tile.items()) if value != 0.0}
            if tiles:
                goods[good] = tiles
        return goods

    # ---- everyone ------------------------------------------------------------------------------------

    def goods_totals(self) -> Dict[GoodId, float]:
        """Quantity held of each good by the agents (edge accounts excluded), goods in name order."""
        goods, quantities = counted_stocks(self.stock_rows.table, self.agent_table)
        order = numpy.argsort(goods, kind="stable")
        quantities, goods = quantities[order], goods[order]
        starts = numpy.flatnonzero(numpy.diff(goods)) + 1 if len(goods) else numpy.zeros(0, dtype=numpy.int64)
        held = {}
        for group, numbers in zip(numpy.split(quantities, starts), numpy.split(goods, starts)):
            if len(group):
                held[self.good_ids.name(int(numbers[0]))] = math.fsum(group.tolist())
        return dict(sorted(held.items()))

    def agents(self) -> List[AgentId]:
        """Every agent the book knows, in name order."""
        return sorted(self.names_of(self.known_agent_numbers().tolist()))

    def holders_of(self, good: GoodId) -> List[AgentId]:
        """Agents (not edge accounts) holding some of the good."""
        number = self.good_ids.find(good)
        if number is None:
            return []
        table = self.stock_rows.table
        rows = int(table.row_count[0])
        held = ((table.good[:rows] == number) & (table.live[:rows] != 0) & (table.quantity[:rows] != 0.0)
                & (self.agent_table.is_edge[table.agent[:rows]] == 0))
        return sorted(set(self.names_of(numpy.unique(table.agent[:rows][held]).tolist())))

    def money_supply(self, currency: CurrencyId) -> float:
        number = self.currency_ids.find(currency)
        if number is None:
            return 0.0
        return math.fsum(currency_values(self.balance_table, self.stride, number, self.agent_table, False).tolist())

    def total(self, currency: CurrencyId) -> float:
        number = self.currency_ids.find(currency)
        if number is None:
            return 0.0
        return math.fsum(currency_values(self.balance_table, self.stride, number, self.agent_table, True).tolist())

    def goods_total(self, good: GoodId) -> float:
        number = self.good_ids.find(good)
        return 0.0 if number is None else math.fsum(good_quantities(self.stock_rows.table, number).tolist())

    def currencies(self) -> List[CurrencyId]:
        agents, wanted = int(self.agent_table.row_count[0]), len(self.currency_ids)
        if not agents or not wanted:
            return []
        seen = self.balance_table.seen[:agents * self.stride].reshape(agents, self.stride)[:, :wanted].any(axis=0)
        return sorted(self.currency_ids.name(number) for number in numpy.flatnonzero(seen).tolist())

    # ---- flows this year -----------------------------------------------------------------------------

    def goods_flow(self, good: GoodId) -> Dict[str, float]:
        number = self.good_ids.find(good)
        if number is None:
            return {}
        table = self.flow_rows.table
        rows = numpy.flatnonzero(table.good[:int(table.row_count[0])] == number)
        flow = {self.purposes.decode(code, reference): quantity for code, reference, quantity in
                zip(table.purpose_code[rows].tolist(), table.purpose_reference[rows].tolist(), table.quantity[rows].tolist())}
        return dict(sorted(flow.items()))

    def goods_flows(self) -> Dict[GoodId, Dict[str, float]]:
        """`goods_flow` for every good that moved this year, in one read."""
        table = self.flow_rows.table
        rows = int(table.row_count[0])
        name, decode = self.good_ids.name_list, self.purposes.decode
        flows: Dict[GoodId, Dict[str, float]] = {}
        for good, code, reference, quantity in zip(table.good[:rows].tolist(), table.purpose_code[:rows].tolist(),
                                                   table.purpose_reference[:rows].tolist(), table.quantity[:rows].tolist()):
            flows.setdefault(name[good], {})[decode(code, reference)] = quantity
        return {good: dict(sorted(flow.items())) for good, flow in flows.items()}

    def _edge_money_cell(self, edge_id: AgentId, currency: CurrencyId):
        cell = self._cell(edge_id, currency)
        return cell if cell is not None and self.balance_table.edge_seen.item(cell) else None

    def edge_volume(self, edge_id: AgentId, currency: CurrencyId) -> float:
        """Gross money in and out through an edge account this year."""
        cell = self._edge_money_cell(edge_id, currency)
        return 0.0 if cell is None else self.balance_table.edge_volume.item(cell)

    def edge_net(self, edge_id: AgentId, currency: CurrencyId) -> float:
        """Money the edge paid into the economy this year, less what it took out."""
        cell = self._edge_money_cell(edge_id, currency)
        return 0.0 if cell is None else self.balance_table.edge_net.item(cell)

    def _edge_goods_row(self, edge_id: AgentId, good: GoodId) -> int:
        agent, good_number = self.agent_ids.find(edge_id), self.good_ids.find(good)
        if agent is None or good_number is None:
            return EMPTY
        return self.edge_goods_rows.find((agent << FIRST_SHIFT) | (good_number << SECOND_SHIFT))

    def edge_goods_volume(self, edge_id: AgentId, good: GoodId) -> float:
        row = self._edge_goods_row(edge_id, good)
        return 0.0 if row == EMPTY else self.edge_goods_rows.table.volume.item(row)

    def edge_goods_net(self, edge_id: AgentId, good: GoodId) -> float:
        row = self._edge_goods_row(edge_id, good)
        return 0.0 if row == EMPTY else self.edge_goods_rows.table.net.item(row)

    def edge_goods_net_by_good(self, edge_id: AgentId) -> Dict[GoodId, float]:
        """`edge_goods_net` for every good the edge carried this year, in one read (a good it did not carry is not in the answer)."""
        agent = self.agent_ids.find(edge_id)
        table = self.edge_goods_rows.table
        rows = int(table.row_count[0])
        if agent is None or not rows:
            return {}
        mine = table.agent[:rows] == agent
        name = self.good_ids.name_list
        return {name[good]: net for good, net in zip(table.good[:rows][mine].tolist(), table.net[:rows][mine].tolist())}

    def edge_goods_agents(self) -> List[AgentId]:
        """Edge accounts that carried goods this year."""
        table = self.edge_goods_rows.table
        return sorted(set(self.names_of(table.agent[:int(table.row_count[0])].tolist())))

    def edge_agents(self) -> List[AgentId]:
        """Edge accounts that carried money this year."""
        agents = int(self.agent_table.row_count[0])
        if not agents:
            return []
        seen = self.balance_table.edge_seen[:agents * self.stride].reshape(agents, self.stride).any(axis=1)
        return sorted(self.names_of(numpy.flatnonzero(seen).tolist()))

    def supply_at_start(self, currency: CurrencyId) -> float:
        """The money supply (edge accounts excluded) when the year's flow records were last reset."""
        number = self.currency_ids.find(currency)
        if number is None or not self.currency_table.supply_seen.item(number):
            return 0.0
        return self.currency_table.supply_at_start.item(number)

    def start_year(self) -> None:
        """Reset the yearly flow records and note the supply; holdings carry."""
        supplies = {currency: self.money_supply(currency) for currency in self.currencies()}
        self.currency_table.supply_seen[:] = 0
        self.currency_table.supply_at_start[:] = 0.0
        for currency, value in supplies.items():
            number = self.currency_ids.find(currency)
            self.currency_table.supply_at_start[number] = value
            self.currency_table.supply_seen[number] = 1
        self.flow_rows.clear()
        self.edge_goods_rows.clear()
        self.balance_table.edge_seen[:] = 0
        self.balance_table.edge_volume[:] = 0.0
        self.balance_table.edge_net[:] = 0.0

    # ---- conservation --------------------------------------------------------------------------------

    def gross_money(self) -> Dict[CurrencyId, float]:
        """Everything ever posted, per currency that has had a posting."""
        table, name = self.currency_table, self.currency_ids.name
        return {name(number): table.gross_posted.item(number) for number in numpy.flatnonzero(
            table.gross_seen[:int(table.row_count[0])]).tolist()}

    def gross_goods(self) -> Dict[GoodId, float]:
        """Everything ever moved, per good that has had a move."""
        table, name = self.good_table, self.good_ids.name
        return {name(number): table.gross_moved.item(number) for number in numpy.flatnonzero(
            table.gross_seen[:int(table.row_count[0])]).tolist()}

    def check_conservation(self, tolerance_share: float) -> ConservationReport:
        """Residual of each currency and good, as a share of everything ever booked in it."""
        money = {currency: _share(self.total(currency), gross) for currency, gross in sorted(self.gross_money().items())}
        goods = {good: _share(self.goods_total(good), gross) for good, gross in sorted(self.gross_goods().items())}
        breaches = tuple(["money %s: %.3g" % item for item in money.items() if item[1] > tolerance_share]
                         + ["goods %s: %.3g" % item for item in goods.items() if item[1] > tolerance_share])
        return ConservationReport(money, goods, breaches)
