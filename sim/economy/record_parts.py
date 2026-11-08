"""The shared shape of the economy record's owned parts, and their round trip to plain JSON for the save.

The record holds one attribute per domain (`record.land`, `record.credit`, ...); each is a dataclass that subclasses
`OwnedRecord`, lives in its owner's module and says there only what is particular to it: which stores are keyed by an
agent id, which are written in id order, which are not saved, and how a field the generic copy cannot read or write
is encoded. The save and the rename walk the dataclass fields, so a new field or a new part needs no list here.
"""
import dataclasses
from typing import Any, Callable, ClassVar, Dict, Iterator, Optional, Tuple

from sim.rekey import rekey

from .record_plain import plain


def sorted_store(store: Dict[Any, Any]) -> Dict[Any, Any]:
    """The store in id order, and each inner dict too."""
    return {key: (dict(sorted(inner.items())) if isinstance(inner, dict) else inner) for key, inner in sorted(store.items())}


def seat_sorted(store: Dict[Any, Any]) -> None:
    if hasattr(store, "seat_sorted"):      # a column store reseats its rows itself
        store.seat_sorted()
        return
    if list(store) != sorted(store):
        held = [(key, store[key]) for key in sorted(store)]
        store.clear()
        store.update(held)


class OwnedRecord:
    """A dataclass of the economy's state with one owner. Subclasses set the class-level tables below."""
    OWNERS: ClassVar[Tuple[str, ...]] = ()           # the sim/economy modules allowed to write this part (tools/check_record_owners.py)
    AGENT_KEYED: ClassVar[Tuple[str, ...]] = ()      # fields holding a store keyed by an agent id (renamed with the agent)
    SAVED_SORTED: ClassVar[Tuple[str, ...]] = ()     # keyed stores the save writes in key order, and so a load reads back in it
    TRANSIENT: ClassVar[Tuple[str, ...]] = ()        # fields not saved: they hold only within-year state, empty between years
    SAVED_KEYS: ClassVar[Dict[str, str]] = {}        # the saved key where it differs from the field name
    ENCODERS: ClassVar[Dict[str, Callable[[Any], Any]]] = {}   # fields the generic copy cannot write
    DECODERS: ClassVar[Dict[str, Callable[[Any], Any]]] = {}   # fields the generic copy cannot read

    def owned_parts(self) -> Iterator["OwnedRecord"]:
        """The parts this record holds, one level down."""
        for each in dataclasses.fields(self):
            value = getattr(self, each.name)
            if isinstance(value, OwnedRecord):
                yield value

    def rename_agent(self, old: str, new: str) -> None:
        """`old` becomes `new` in every store of this record and its parts that is keyed by an agent id."""
        for name in self.AGENT_KEYED:
            setattr(self, name, rekey(getattr(self, name), old, new))
        for part in self.owned_parts():
            part.rename_agent(old, new)

    def sort_in_saved_order(self) -> None:
        """Re-seat the keyed stores the save writes in key order, in place, so a live game iterates them as a loaded one does."""
        for name in self.SAVED_SORTED:
            store = getattr(self, name)
            seat_sorted(store)
            for inner in store.values():
                if isinstance(inner, dict):
                    seat_sorted(inner)
        for part in self.owned_parts():
            part.sort_in_saved_order()

    def saved_fields(self, encoders: Optional[Dict[str, Callable[[Any], Any]]] = None) -> Dict[str, Any]:
        """Plain data, a field each (`dataclasses.fields`), the stores in SAVED_SORTED written in key order, each part nested.
        `encoders` add to or replace the class's own for this call."""
        encode = {**self.ENCODERS, **(encoders or {})}
        saved: Dict[str, Any] = {}
        for each in dataclasses.fields(self):
            name = each.name
            value = getattr(self, name)
            if name in self.TRANSIENT:
                continue
            if name in encode:
                saved[self.SAVED_KEYS.get(name, name)] = encode[name](value)
            elif isinstance(value, OwnedRecord):
                saved[name] = value.saved_fields()
            else:
                saved[name] = plain(sorted_store(value) if name in self.SAVED_SORTED else value)
        return saved

    @classmethod
    def from_saved_fields(cls, record: Dict[str, Any]):
        """The inverse of `saved_fields`; a field that is itself a part is read by that part's own class."""
        values = {}
        for each in dataclasses.fields(cls):
            name = each.name
            if name in cls.TRANSIENT:
                continue
            data = record[cls.SAVED_KEYS.get(name, name)]
            if name in cls.DECODERS:
                values[name] = cls.DECODERS[name](data)
            elif isinstance(each.type, type) and issubclass(each.type, OwnedRecord):
                values[name] = each.type.from_saved_fields(data)
            else:
                values[name] = plain(data)
        return cls(**values)
