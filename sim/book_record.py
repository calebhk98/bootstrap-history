"""The book's save file, merge and rename: a mixin of `Book` (sim/book.py), which owns the layout."""
from typing import Callable, Dict, Iterable

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
    def rename_agent(self, old: AgentId, new: AgentId) -> None:
        """Everything `old` holds becomes `new`'s (added to what `new` holds); no posting is made, so no total moves."""
        old_row = self._row.pop(old, None)
        if old_row is None:
            return
        for currency, column in self._balance.items():
            if self._seen[currency][old_row]:
                new_row = self._row_of(new)
                column[new_row] = (column[new_row] if self._seen[currency][new_row] else 0.0) + column[old_row]
                self._seen[currency][new_row] = 1
                self._seen[currency][old_row] = 0
                column[old_row] = 0.0
        self._names[old_row] = None
        self._edge[old_row] = 0
        moved = [(slot, self._slot_key[slot]) for by_tile in self._agent_slots.pop(old, {}).values() for slot in by_tile.values()]
        for slot, key in moved:
            _agent, good, tile = key
            new_slot = self._slot.get((new, good, tile))
            del self._slot[key]
            if new_slot is not None:
                self._qty[new_slot] += self._qty[slot]
                self._slot_key[slot] = None
                self._slot_row[slot] = -1
                self._qty[slot] = 0.0
                self._good_slots[good].remove(slot)
                continue
            self._slot[(new, good, tile)] = slot
            self._slot_key[slot] = (new, good, tile)
            self._slot_row[slot] = self._row_of(new)
            self._agent_slots.setdefault(new, {}).setdefault(good, {})[tile] = slot

    def to_record(self, only: Iterable[CurrencyId] = None, skip: Iterable[CurrencyId] = ()) -> dict:
        """The book as plain data; `only` keeps just those currencies (goods are left out then), `skip` drops some."""
        if only is None and not skip:
            return self._record_of(lambda currency: True, True, False)
        wanted = None if only is None else set(only)
        dropped = set(skip)
        return self._record_of(lambda currency: (wanted is None or currency in wanted) and currency not in dropped,
                               wanted is None, True)

    def _money_record(self, keep: Callable[[str], bool]) -> dict:
        money: dict = {}
        names = self._names
        for currency in sorted(self._balance):
            if not keep(currency):
                continue
            column, seen = self._balance[currency], self._seen[currency]
            for row in range(len(names)):
                if seen[row]:
                    money.setdefault(names[row], {})[currency] = column[row]
        return {agent: dict(sorted(by_currency.items())) for agent, by_currency in sorted(money.items())}

    def _record_of(self, keep: Callable[[str], bool], with_goods: bool, filtered: bool) -> dict:
        goods: dict = {}
        if with_goods:
            quantities = self._qty
            for key in sorted(self._slot):
                agent, good, tile = key
                goods.setdefault(agent, {}).setdefault(good, {})[tile] = quantities[self._slot[key]]
        record = {
            "money": self._money_record(keep),
            "goods": goods,
            "gross_money": {currency: value for currency, value in sorted(self._gross_money.items()) if keep(currency)},
            "gross_goods": dict(sorted(self._gross_goods.items())) if with_goods else {},
            "goods_by_purpose": _sorted_nested(self._goods_by_purpose) if with_goods else {},
            "supply_at_start": {currency: value for currency, value in sorted(self._supply_at_start.items()) if keep(currency)},
        }
        for name, column in (("edge_money_volume", 0), ("edge_money_net", 1)):
            record[name] = _pairs_to_nested(self._edge_money, column, keep)
        for name, column in (("edge_goods_volume", 0), ("edge_goods_net", 1)):
            record[name] = _pairs_to_nested(self._edge_goods, column, lambda good: True) if with_goods else {}
        return record

    def absorb(self, other) -> None:
        """Take over everything `other` holds and has booked, its currencies added to this book's."""
        for currency, column in other._balance.items():
            seen = other._seen[currency]
            for row, agent in enumerate(other._names):
                if agent is not None and seen[row]:
                    mine = self._row_of(agent)
                    mine_column = self._column(currency)
                    mine_seen = self._seen[currency]
                    mine_column[mine] = (mine_column[mine] if mine_seen[mine] else 0.0) + column[row]
                    mine_seen[mine] = 1
        for (agent, good, tile), slot in other._slot.items():
            self._set_stock(agent, good, tile, self.stock(agent, good, tile) + other._qty[slot])
        for mine, theirs in ((self._gross_money, other._gross_money), (self._gross_goods, other._gross_goods),
                             (self._supply_at_start, other._supply_at_start)):
            for key, value in theirs.items():
                mine[key] = mine.get(key, 0.0) + value
        _add_nested(self._goods_by_purpose, other._goods_by_purpose)
        for mine, theirs in ((self._edge_money, other._edge_money), (self._edge_goods, other._edge_goods)):
            for key, both in theirs.items():
                held = mine.get(key)
                if held is None:
                    mine[key] = list(both)
                else:
                    held[0] += both[0]
                    held[1] += both[1]

    @classmethod
    def from_record(cls, record: dict):
        book = cls()
        for agent, by_currency in sorted(record["money"].items()):
            for currency, value in sorted(by_currency.items()):
                book._put_money(agent, currency, value)
        for agent, by_good in sorted(record["goods"].items()):
            for good, by_tile in sorted(by_good.items()):
                for tile, value in sorted(by_tile.items()):
                    book._set_stock(agent, good, tile, value)
        book._gross_money = dict(record["gross_money"])
        book._gross_goods = dict(record["gross_goods"])
        book._goods_by_purpose = _sorted_nested(record["goods_by_purpose"])
        for flow, volume_name, net_name in ((book._edge_money, "edge_money_volume", "edge_money_net"),
                                            (book._edge_goods, "edge_goods_volume", "edge_goods_net")):
            for agent, by_name in record[volume_name].items():
                for name, value in by_name.items():
                    flow[(agent, name)] = [value, record[net_name].get(agent, {}).get(name, 0.0)]
            for agent, by_name in record[net_name].items():
                for name, value in by_name.items():
                    flow.setdefault((agent, name), [0.0, value])
        book._supply_at_start = dict(record["supply_at_start"])
        return book
