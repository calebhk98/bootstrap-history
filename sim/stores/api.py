"""The stores package's only door."""

WALL = "two-way"  # nothing here imports sim/engine/; the engine bridge hands it the declarations it loads from data

from .book import ModStore, StoreBook, StoreView
from .commands import WriteStore
from .rules import ACTOR, ACTOR_PAIR, KEYED_BY, TILE, StoreSpec, check_spec, declare_all, store_key
