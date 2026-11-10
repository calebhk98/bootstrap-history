"""The book's save file, merge and rename: a mixin of `Book` (sim/book.py), which owns the layout (sim/book_store.py).

The record is plain data keyed by names (so it reads the same whatever the numbers are); `from_record` admits the names again."""
from typing import Callable, Dict, Iterable

import numpy

from sim.book_commit import create_slot, record_edge_goods
from sim.book_goods_plain import goods_nested
from sim.book_index import EMPTY, index_add, pack_key
from sim.book_tables import FREE
from sim.book_types import AgentId, CurrencyId


def _sorted_nested(mapping: dict) -> dict:
    return {key: dict(sorted(inner.items())) for key, inner in sorted(mapping.items())}


def _add_nested(into: dict, source: dict) -> None:
    for key, inner in source.items():
        held = into.get(key)
        if held is None:
            held = into[key] = {}
        for name, value in inner.items():
            held[name] = held.get(name, 0.0) + value


def _pairs_to_nested(pairs: Dict[tuple, list], column: int, keep: Callable[[str], bool]) -> dict:
    """{(agent, name): [volume, net]} as {agent: {name: value}} in name order, keeping the names `keep` passes."""
    out: dict = {}
    for (agent, name), both in sorted(pairs.items()):
        if keep(name):
            out.setdefault(agent, {})[name] = both[column]
    return out


class BookRecord:
    # ---- writing single cells (a load, a merge) -----------------------------------------------------

    def _put_money(self, agent: AgentId, currency: CurrencyId, value: float) -> None:
        number, currency_number = self.agent_number(agent), self.currency_number(currency)
        cell = number * self.stride + currency_number
        self.balance_table.amount[cell] = value
        self.balance_table.seen[cell] = 1
        self.agent_table.known[number] = 1

    def _slot_of(self, agent: AgentId, good: str, tile: str) -> int:
        """The slot for the cell, made (at zero, chained to the agent) when there is none."""
        number, good_number, tile_number = self.agent_number(agent), self.good_number(good), self.tile_number(tile)
        key = pack_key(number, good_number, tile_number)
        slot = self.stock_rows.find(key)
        if slot == EMPTY:
            self.stock_rows.reserve(1)
            slot = create_slot(self.stock_rows.table, self.stock_rows.index, self.agent_table, key)
        self.agent_table.known[number] = 1
        return slot

    def _set_stock(self, agent: AgentId, good: str, tile: str, value: float) -> None:
        slot = self._slot_of(agent, good, tile)
        self.stock_rows.table.quantity[slot] = value

    def _set_edge_money(self, agent: AgentId, currency: CurrencyId, volume: float, net: float) -> None:
        cell = self.agent_number(agent) * self.stride + self.currency_number(currency)
        self.balance_table.edge_seen[cell] = 1
        self.balance_table.edge_volume[cell] = volume
        self.balance_table.edge_net[cell] = net

    def _set_edge_goods(self, agent: AgentId, good: str, volume: float, net: float) -> None:
        self.edge_goods_rows.reserve(1)
        record_edge_goods(self.edge_goods_rows.table, self.edge_goods_rows.index, self.agent_number(agent),
                          self.good_number(good), volume, net)

    def _add_edge_money(self, agent: AgentId, currency: CurrencyId, volume: float, net: float) -> None:
        cell = self.agent_number(agent) * self.stride + self.currency_number(currency)
        if self.balance_table.edge_seen[cell]:
            self.balance_table.edge_volume[cell] += volume
            self.balance_table.edge_net[cell] += net
        else:
            self._set_edge_money(agent, currency, volume, net)

    # ---- rename --------------------------------------------------------------------------------------

    def rename_agent(self, old: AgentId, new: AgentId) -> None:
        """Everything `old` holds becomes `new`'s (added to what `new` holds); no posting is made, so no total moves."""
        old_number = self.agent_ids.find(old)
        if old_number is None or not self.agent_table.known[old_number]:
            return
        self.agent_table.known[old_number] = 0
        balances, stride = self.balance_table, self.stride
        for currency_number in range(len(self.currency_ids)):
            old_cell = old_number * stride + currency_number
            if balances.seen[old_cell]:
                new_number = self.agent_number(new)
                self.agent_table.known[new_number] = 1
                new_cell = new_number * stride + currency_number
                balances = self.balance_table
                balances.amount[new_cell] = (balances.amount[new_cell] if balances.seen[new_cell] else 0.0) + balances.amount[old_cell]
                balances.seen[new_cell] = 1
                balances.seen[old_cell] = 0
                balances.amount[old_cell] = 0.0
        self._move_slots(old_number, new)

    def _move_slots(self, old_number: int, new: AgentId) -> None:
        """Give the old agent's stock slots to `new`: re-keyed, or merged into a slot `new` already has. They are moved in
        the order the old agent's slots were grouped by good (the order the book always gave them to `new`)."""
        agents, table = self.agent_table, self.stock_rows.table
        by_good: Dict[int, list] = {}
        slot = int(agents.first_slot[old_number])
        while slot != FREE:
            by_good.setdefault(int(table.good[slot]), []).append(slot)
            slot = int(table.next_in_agent[slot])
        agents.first_slot[old_number] = FREE
        agents.last_slot[old_number] = FREE
        if not by_good:
            return
        moving = [slot for slots in by_good.values() for slot in slots]
        table.live[moving] = 0
        self.stock_rows.rebuild()
        new_number = self.agent_number(new)
        agents = self.agent_table
        agents.known[new_number] = 1
        for slot in moving:
            new_key = pack_key(new_number, int(table.good[slot]), int(table.tile[slot]))
            existing = self.stock_rows.find(new_key)
            if existing != EMPTY:
                table.quantity[existing] += table.quantity[slot]
                table.quantity[slot] = 0.0
                continue
            table.key[slot] = new_key
            table.agent[slot] = new_number
            table.next_in_agent[slot] = FREE
            table.live[slot] = 1
            last = int(agents.last_slot[new_number])
            if last == FREE:
                agents.first_slot[new_number] = slot
            else:
                table.next_in_agent[last] = slot
            agents.last_slot[new_number] = slot
            index_add(table.key, self.stock_rows.index, slot)

    # ---- save ----------------------------------------------------------------------------------------

    def to_record(self, only: Iterable[CurrencyId] = None, skip: Iterable[CurrencyId] = ()) -> dict:
        """The book as plain data; `only` keeps just those currencies (goods are left out then), `skip` drops some."""
        if only is None and not skip:
            return self._record_of(lambda currency: True, True)
        wanted = None if only is None else set(only)
        dropped = set(skip)
        return self._record_of(lambda currency: (wanted is None or currency in wanted) and currency not in dropped, wanted is None)

    def _money_record(self, keep: Callable[[str], bool]) -> dict:
        agents, wanted = int(self.agent_table.row_count[0]), len(self.currency_ids)
        money: dict = {}
        if agents and wanted:
            seen = self.balance_table.seen[:agents * self.stride].reshape(agents, self.stride)[:, :wanted]
            numbers, currencies = numpy.nonzero(seen)
            amounts = self.balance_table.amount[:agents * self.stride].reshape(agents, self.stride)
            for number, currency_number in zip(numbers.tolist(), currencies.tolist()):
                currency = self.currency_ids.name(currency_number)
                if keep(currency):
                    money.setdefault(self.agent_ids.name(number), {})[currency] = amounts.item(number, currency_number)
        return {agent: dict(sorted(by_currency.items())) for agent, by_currency in sorted(money.items())}

    def _goods_record(self) -> dict:
        table = self.stock_rows.table
        live = numpy.flatnonzero(table.live[:int(table.row_count[0])])
        return goods_nested(table.agent[live], table.good[live], table.tile[live], table.quantity[live],
                            self.agent_ids, self.good_ids, self.tile_ids)

    def _purpose_record(self) -> dict:
        table = self.flow_rows.table
        rows = slice(0, int(table.row_count[0]))
        flows: dict = {}
        for good, code, reference, quantity in zip(table.good[rows].tolist(), table.purpose_code[rows].tolist(),
                                                   table.purpose_reference[rows].tolist(), table.quantity[rows].tolist()):
            flows.setdefault(self.good_ids.name(good), {})[self.purposes.decode(code, reference)] = quantity
        return _sorted_nested(flows)

    def _edge_money_pairs(self) -> Dict[tuple, list]:
        agents, wanted = int(self.agent_table.row_count[0]), len(self.currency_ids)
        pairs: Dict[tuple, list] = {}
        if agents and wanted:
            seen = self.balance_table.edge_seen[:agents * self.stride].reshape(agents, self.stride)[:, :wanted]
            volume = self.balance_table.edge_volume[:agents * self.stride].reshape(agents, self.stride)
            net = self.balance_table.edge_net[:agents * self.stride].reshape(agents, self.stride)
            for number, currency_number in zip(*[found.tolist() for found in numpy.nonzero(seen)]):
                pairs[(self.agent_ids.name(number), self.currency_ids.name(currency_number))] = [
                    volume.item(number, currency_number), net.item(number, currency_number)]
        return pairs

    def _edge_goods_pairs(self) -> Dict[tuple, list]:
        table = self.edge_goods_rows.table
        rows = slice(0, int(table.row_count[0]))
        return {(self.agent_ids.name(agent), self.good_ids.name(good)): [volume, net] for agent, good, volume, net in zip(
            table.agent[rows].tolist(), table.good[rows].tolist(), table.volume[rows].tolist(), table.net[rows].tolist())}

    def _supply_at_start_dict(self) -> Dict[CurrencyId, float]:
        table = self.currency_table
        return {self.currency_ids.name(number): table.supply_at_start.item(number) for number in numpy.flatnonzero(
            table.supply_seen[:int(table.row_count[0])]).tolist()}

    def _record_of(self, keep: Callable[[str], bool], with_goods: bool) -> dict:
        record = {
            "money": self._money_record(keep),
            "goods": self._goods_record() if with_goods else {},
            "gross_money": {currency: value for currency, value in sorted(self.gross_money().items()) if keep(currency)},
            "gross_goods": dict(sorted(self.gross_goods().items())) if with_goods else {},
            "goods_by_purpose": self._purpose_record() if with_goods else {},
            "supply_at_start": {currency: value for currency, value in sorted(self._supply_at_start_dict().items()) if keep(currency)},
        }
        if with_goods:
            record["numbering"] = self.numbering_state()
        for name, column in (("edge_money_volume", 0), ("edge_money_net", 1)):
            record[name] = _pairs_to_nested(self._edge_money_pairs(), column, keep)
        for name, column in (("edge_goods_volume", 0), ("edge_goods_net", 1)):
            record[name] = _pairs_to_nested(self._edge_goods_pairs(), column, lambda good: True) if with_goods else {}
        return record

    # ---- merge ---------------------------------------------------------------------------------------

    def absorb(self, other) -> None:
        """Take over everything `other` holds and has booked, its currencies added to this book's."""
        agents = int(other.agent_table.row_count[0])
        for currency_number in range(len(other.currency_ids)):
            currency = other.currency_ids.name(currency_number)
            for number in range(agents):
                cell = number * other.stride + currency_number
                if other.agent_table.known[number] and other.balance_table.seen[cell]:
                    agent = other.agent_ids.name(number)
                    mine = self.balance(agent, currency) if self._seen_cell(agent, currency) else 0.0
                    self._put_money(agent, currency, mine + other.balance_table.amount.item(cell))
        table = other.stock_rows.table
        for slot in range(int(table.row_count[0])):
            if table.live[slot]:
                agent, good, tile = (other.agent_ids.name(int(table.agent[slot])), other.good_ids.name(int(table.good[slot])),
                                     other.tile_ids.name(int(table.tile[slot])))
                self._set_stock(agent, good, tile, self.stock(agent, good, tile) + table.quantity.item(slot))
        self._absorb_totals(other)

    def _seen_cell(self, agent: AgentId, currency: CurrencyId) -> bool:
        cell = self._cell(agent, currency)
        return cell is not None and bool(self.balance_table.seen[cell])

    def _absorb_totals(self, other) -> None:
        """Add the other book's gross totals, supply, purpose flows and edge records to this book's."""
        for currency, value in other.gross_money().items():
            self._set_gross_money(currency, self.gross_money().get(currency, 0.0) + value)
        for good, value in other.gross_goods().items():
            self._set_gross_goods(good, self.gross_goods().get(good, 0.0) + value)
        for currency, value in other._supply_at_start_dict().items():
            self._set_supply_at_start(currency, self._supply_at_start_dict().get(currency, 0.0) + value)
        mine = self._purpose_record()
        _add_nested(mine, other._purpose_record())
        self._set_purpose_flows(mine)
        for (agent, currency), (volume, net) in other._edge_money_pairs().items():
            self._add_edge_money(agent, currency, volume, net)
        held = self._edge_goods_pairs()
        for (agent, good), (volume, net) in other._edge_goods_pairs().items():
            before = held.get((agent, good))
            self._set_edge_goods_pair(agent, good, volume if before is None else before[0] + volume,
                                      net if before is None else before[1] + net)

    def _set_gross_money(self, currency: CurrencyId, value: float) -> None:
        number = self.currency_number(currency)
        self.currency_table.gross_posted[number] = value
        self.currency_table.gross_seen[number] = 1

    def _set_gross_goods(self, good: str, value: float) -> None:
        number = self.good_number(good)
        self.good_table.gross_moved[number] = value
        self.good_table.gross_seen[number] = 1

    def _set_supply_at_start(self, currency: CurrencyId, value: float) -> None:
        number = self.currency_number(currency)
        self.currency_table.supply_at_start[number] = value
        self.currency_table.supply_seen[number] = 1

    def _set_purpose_flows(self, flows: dict) -> None:
        """Replace this year's purpose flows by {good: {purpose text: quantity}}."""
        self.flow_rows.clear()
        for good, by_purpose in flows.items():
            number = self.good_number(good)
            for purpose, quantity in by_purpose.items():
                code, reference = self.purposes.encode(purpose)
                self.flow_rows.reserve(1)
                self._append_flow(number, code, reference, quantity)

    def _append_flow(self, good: int, code: int, reference: int, quantity: float) -> None:
        from sim.book_commit import add_flow
        add_flow(self.flow_rows.table, self.flow_rows.index, good, code, reference, quantity)

    def _set_edge_goods_pair(self, agent: AgentId, good: str, volume: float, net: float) -> None:
        """Set an edge account's goods record to exactly these figures (made when absent)."""
        row = self._edge_goods_row(agent, good)
        if row == EMPTY:
            self._set_edge_goods(agent, good, volume, net)
        else:
            self.edge_goods_rows.table.volume[row] = volume
            self.edge_goods_rows.table.net[row] = net

    # ---- load ----------------------------------------------------------------------------------------

    @classmethod
    def from_record(cls, record: dict):
        book = cls()
        if record.get("numbering"):
            book.adopt_numbering(record["numbering"])
        for agent, by_currency in sorted(record["money"].items()):
            for currency, value in sorted(by_currency.items()):
                book._put_money(agent, currency, value)
        for agent, by_good in sorted(record["goods"].items()):
            for good, by_tile in sorted(by_good.items()):
                for tile, value in sorted(by_tile.items()):
                    book._set_stock(agent, good, tile, value)
        for currency, value in record["gross_money"].items():
            book._set_gross_money(currency, value)
        for good, value in record["gross_goods"].items():
            book._set_gross_goods(good, value)
        book._set_purpose_flows(_sorted_nested(record["goods_by_purpose"]))
        for volume_name, net_name, set_flow, nets_of in (
                ("edge_money_volume", "edge_money_net", book._set_edge_money, record["edge_money_net"]),
                ("edge_goods_volume", "edge_goods_net", book._set_edge_goods, record["edge_goods_net"])):
            volumes = record[volume_name]
            for agent, by_name in volumes.items():
                for name, value in by_name.items():
                    set_flow(agent, name, value, nets_of.get(agent, {}).get(name, 0.0))
            for agent, by_name in nets_of.items():
                for name, value in by_name.items():
                    if name not in volumes.get(agent, {}):
                        set_flow(agent, name, 0.0, value)
        for currency, value in record["supply_at_start"].items():
            book._set_supply_at_start(currency, value)
        return book
