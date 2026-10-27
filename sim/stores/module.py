"""The stores module: the declared key/value stores of a game, saved with it, written by the commands sent to it."""
from typing import Any, Dict, List, Optional

from sim.assembly.api import Module

from .book import StoreBook
from .commands import WriteStore
from .rules import StoreSpec, declare_all


class Stores(Module):

	_declared: Optional[Dict[str, StoreSpec]] = None

	def declared(self) -> Dict[str, StoreSpec]:
		"""The game's stores, from every provider of the `store_declarations` point (the base game's, the mods' data, mod
		code); asked on first use, once the engine's data views answer."""
		if self._declared is None:
			self._declared = declare_all(self.needs.store_declarations())
		return self._declared

	def store_book(self) -> StoreBook:
		"""Every declared store over the saved values; made on each read, since a load replaces the saved dictionary."""
		return StoreBook(self.declared(), self.world.values)

	def store(self, name: str) -> Dict[str, Any]:
		"""One store as it stands: {default, values: {key: value}}."""
		declared = self.store_book().view(name)
		return {"default": declared.spec.default, "values": dict(declared.values)}

	def write_store(self, command: WriteStore) -> None:
		self.store_book().write(command.store, command.key, command.value, command.owner)

	def provide_base_stores(self) -> List[StoreSpec]:
		"""The base game's own stores (data/world/stores.json)."""
		return list(self.needs.base_store_declarations())

	def provide_data_stores(self) -> List[StoreSpec]:
		"""The stores the installed mods declare in their data/stores.json."""
		return list(self.needs.data_store_declarations())
