"""The content module: the mods directory a game is over, and what the mods installed there contribute to the game's data."""
from typing import Any, Dict, List, Tuple

from sim.assembly.api import Module
from sim.stores.api import StoreSpec

from . import views
from .commands import OpenContent


class Content(Module):

	directory: str = ""   # set by OpenContent; a save does not hold it (the game is rebuilt over the same mods). Empty: no mods installed

	def open_content(self, command: OpenContent) -> None:
		self.directory = command.directory

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
