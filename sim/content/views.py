"""What the installed mods of one directory contribute, as plain functions of that directory."""
from typing import Any, Dict, List, Tuple

from sim.default_civilisation import REPOSITORY_ROOT
from sim.stores.api import StoreSpec

from . import actor_kinds_data, mod_stores, need_data
from .mods import get_ordered_mods


def installed_mod_ids(directory: str) -> Tuple[str, ...]:
	"""The ids of the installed mods in load order."""
	return tuple(manifest.id for manifest in get_ordered_mods(directory))


def map_overlays(directory: str) -> List[Tuple[str, str]]:
	"""[(mod id, directory)] of the installed mods, in load order: the map overlays the base map is merged with."""
	return [(manifest.id, manifest.directory) for manifest in get_ordered_mods(directory)]


def household_need_data(directory: str) -> Dict[str, Dict[str, Any]]:
	"""{"needs", "goods"}: the base game's household needs and the goods that serve them, with each mod's of `directory`."""
	return need_data.load_needs(REPOSITORY_ROOT, directory)


def declared_actor_kinds(directory: str) -> Dict[str, Any]:
	"""{kind id: class} for the actor kinds the mods of `directory` declare in data."""
	return actor_kinds_data.declared_kinds(directory)


def data_store_declarations(directory: str) -> List[StoreSpec]:
	"""[StoreSpec] the mods of `directory` declare in their data/stores.json, in mod load order."""
	return mod_stores.data_declarations(directory)
