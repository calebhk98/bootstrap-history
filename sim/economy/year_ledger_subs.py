"""The second part of a pair-table key, as a name and as numbers.

A pair row is (agent, subkey, extra). What the subkey stands for differs by table; one small class each says how a name the
readers use becomes (subkey, extra) and back. `find` never numbers anything (a name nobody has met is absent); `make` numbers it."""
from typing import Optional, Sequence, Tuple

from sim.book_purposes import REFERENCE_PREFIXES

SALE_PREFIX = "sale of "


class GoodSub:
    """A good, numbered by the book."""

    def __init__(self, tables) -> None:
        self._tables = tables

    def find(self, sub) -> Optional[Tuple[int, int]]:
        number = self._tables.book.good_ids.numbers.get(sub)
        return None if number is None else (number, 0)

    def make(self, sub) -> Tuple[int, int]:
        return (self._tables.book.good_number(sub), 0)

    def name(self, subkey: int, extra: int) -> str:
        return self._tables.book.good_ids.name_list[subkey]

    def names(self, subkeys: Sequence[int], extras: Sequence[int]) -> list:
        return list(map(self._tables.book.good_ids.name_list.__getitem__, subkeys))


class TradeSub:
    """A trade, numbered by the market memory."""

    def __init__(self, tables) -> None:
        self._tables = tables

    def find(self, sub) -> Optional[Tuple[int, int]]:
        number = self._tables.markets.trades.numbers.get(sub)
        return None if number is None else (number, 0)

    def make(self, sub) -> Tuple[int, int]:
        return (self._tables.trade_number(sub), 0)

    def name(self, subkey: int, extra: int) -> str:
        return self._tables.markets.trades.name_list[subkey]

    def names(self, subkeys: Sequence[int], extras: Sequence[int]) -> list:
        return list(map(self._tables.markets.trades.name_list.__getitem__, subkeys))


class ForeignSub:
    """What money across the border was for: the good of a sale ("sale of wheat" is `wheat`) or any other purpose text, kept as
    the purpose's (template, reference) in the book's numbering. A purpose the book never posted is numbered when written
    through a view; the settlement and posting paths only meet purposes the book already numbered."""

    def __init__(self, tables) -> None:
        self._tables = tables

    def find(self, sub) -> Optional[Tuple[int, int]]:
        purposes = self._tables.book.purposes
        for text in (SALE_PREFIX + sub, sub):
            template, reference = next(((prefix, text[len(prefix):]) for prefix in REFERENCE_PREFIXES if text.startswith(prefix)),
                                       (text, ""))
            template_number, reference_number = purposes.templates.numbers.get(template), purposes.references.numbers.get(reference)
            if template_number is not None and reference_number is not None:
                return (template_number, reference_number)
        return None

    def make(self, sub) -> Tuple[int, int]:
        found = self.find(sub)
        return found if found is not None else tuple(self._tables.purpose_code(SALE_PREFIX + sub))

    def name(self, subkey: int, extra: int) -> str:
        text = self._tables.book.purposes.decode(subkey, extra)
        return text[len(SALE_PREFIX):] if text.startswith(SALE_PREFIX) else text

    def names(self, subkeys: Sequence[int], extras: Sequence[int]) -> list:
        return list(map(self.name, subkeys, extras))


class LabourMarketSub:
    """A labour market (a trade and a labour area) of the market memory; the key shows both parts."""

    def __init__(self, tables) -> None:
        self._tables = tables

    def find(self, sub) -> Optional[Tuple[int, int]]:
        number = self._tables.markets.labour_numbers.get(sub[0] + "|" + sub[1])
        return None if number is None else (number, 0)

    def make(self, sub) -> Tuple[int, int]:
        return (self._tables.labour_market_number(sub[0], sub[1]), 0)

    def name(self, subkey: int, extra: int):
        trade, _separator, area = self._tables.markets.labour_markets.name_list[subkey].partition("|")
        return (trade, area)

    def names(self, subkeys: Sequence[int], extras: Sequence[int]) -> list:
        return list(map(self.name, subkeys, extras))
