"""The stores module for a test: `stores_module(specs)` is the real module over plain values, `base_book(saved)` a store book over the
base game's declared stores, for a test host that has no assembly. Both read and write the plain dictionary `saved`
({store: {key: value}}), as the stores module does over its saved values.

    host = StoreHost(StoreSpec("acme:mana", "acme", "tile", 0.0, "mana"))   # `host.stores`, and `host.send(WriteStore(...))`"""
from typing import Any, Dict, Optional

from sim.engine import mod_stores
from sim.stores.api import StoreBook, StoreSpec
from sim.stores.module import Stores
from sim.stores.state import StoresWorld
from sim.tests import module_harness


def base_book(saved: Optional[Dict[str, Dict[str, Any]]] = None) -> StoreBook:
    return StoreBook({spec.name: spec for spec in mod_stores.base_declarations()}, {} if saved is None else saved)


def stores_module(specs: Any = (), saved: Optional[Dict[str, Dict[str, Any]]] = None) -> Stores:
    """The stores module declaring `specs` (one provider's answer to the `store_declarations` point) over the values in `saved`."""
    return module_harness.build(Stores, views={"store_declarations": lambda: [list(specs)]},
                                world=StoresWorld(values={} if saved is None else saved), module_id="stores")


class StoreHost:
    """A game with nothing but its stores: `stores` is the book, and `stores_module` applies a sent `WriteStore`."""

    def __init__(self, *specs: StoreSpec):
        self.stores_module = stores_module(specs)

    @property
    def stores(self) -> StoreBook:
        return self.stores_module.store_book()
