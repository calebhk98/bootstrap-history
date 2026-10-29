"""What the installed mods of one directory contribute, as plain functions of that directory."""
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Tuple

from sim.default_civilisation import REPOSITORY_ROOT
from sim.stores.api import StoreSpec

from . import win_condition_labels as labels_data
from . import actor_kinds_data, foreign_economies, mod_stores, need_data, tech_effects, trades
from .catalog import Trade
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


def trade_records(directory: str) -> Dict[str, Trade]:
    """{trade id: the trade registry's record (family, training years, the rest of its file)}."""
    return trades.trade_registry(directory)


def tech_effect_table(directory: str) -> Dict[str, Any]:
    """{node id: what finishing it does to the society}."""
    return tech_effects.load_tech_effects(directory)


def foreign_economy_records(directory: str) -> Tuple[Dict[str, Any], ...]:
    """The economies the data file names, with the mods of `directory` applied."""
    return foreign_economies.foreign_economy_records(directory)


def not_traded_materials(directory: str) -> FrozenSet[str]:
    """Materials that cannot cross a border."""
    return foreign_economies.not_traded_materials(directory)


def win_condition_labels(directory: str) -> Dict[str, str]:
    """Metric to the sentence template that says what a win condition on it asks for."""
    return labels_data.win_condition_labels(directory)
