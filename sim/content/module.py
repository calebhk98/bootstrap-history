"""The content module: the mods directory a game is over, and what the mods installed there contribute to the game's data."""
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Tuple

from sim.assembly.api import Module
from sim.stores.api import StoreSpec

from . import views
from .catalog import Trade
from .commands import OpenContent
from .trades import trade_family, trade_notes, trades_absent


class Content(Module):

	directory: str = ""   # set by OpenContent; a save does not hold it (the game is rebuilt over the same mods). Empty: no mods installed

	def setup(self) -> None:
		self.loaded: Dict[Tuple[str, str], Any] = {}

	def open_content(self, command: OpenContent) -> None:
		self.directory = command.directory

	def _once(self, name: str, load: Callable[[str], Any]) -> Any:
		"""What `load` answers for this game's directory, read once: the registry and the effects table are files that do not
		change while a game runs."""
		key = (name, self.directory)
		if key not in self.loaded:
			self.loaded[key] = load(self.directory)
		return self.loaded[key]

	def mods_directory(self) -> str:
		"""The directory whose mods this game is built over; empty when it was built over none."""
		return self.directory

	def installed_mod_ids(self) -> Tuple[str, ...]:
		return views.installed_mod_ids(self.mods_directory())

	def map_overlays(self) -> List[Tuple[str, str]]:
		return views.map_overlays(self.mods_directory())

	def household_need_data(self) -> Dict[str, Dict[str, Any]]:
		return views.household_need_data(self.mods_directory())

	def declared_actor_kinds(self) -> Dict[str, Any]:
		return views.declared_actor_kinds(self.mods_directory())

	def data_store_declarations(self) -> List[StoreSpec]:
		return views.data_store_declarations(self.mods_directory())

	def trade_records(self) -> Dict[str, Trade]:
		return self._once("trade_records", views.trade_records)

	def trade_notes(self) -> Dict[str, str]:
		return trade_notes(self.trade_records())

	def trades_absent(self) -> FrozenSet[str]:
		return trades_absent(self.trade_records())

	def trade_family(self, trade: str) -> str:
		return trade_family(self.trade_records(), trade)

	def tech_effects(self, node_id: str) -> Optional[Dict[str, Any]]:
		"""What finishing `node_id` does to the society, or None."""
		return self._once("tech_effects", views.tech_effect_table).get(node_id)

	def foreign_economy_records(self) -> Tuple[Dict[str, Any], ...]:
		return views.foreign_economy_records(self.directory)

	def not_traded_materials(self) -> FrozenSet[str]:
		return views.not_traded_materials(self.directory)
