"""The trade registry of a mods directory, and the plain facts read off it."""
from typing import Dict, FrozenSet, Mapping

from sim.default_civilisation import REPOSITORY_ROOT

from .catalog import Trade, load_mod_tree_nodes, load_production_catalog, load_trade_registry
from .tree_source import NO_MODS_DIRECTORY

DEFAULT_FAMILY = "craft"   # the family of a trade the registry does not name


def trade_registry(directory: str) -> Dict[str, Trade]:
    """{trade id: Trade} of the base game with the mods of `directory` applied; an empty `directory` installs none."""
    mods_directory = directory or NO_MODS_DIRECTORY
    return load_trade_registry(REPOSITORY_ROOT, load_production_catalog(REPOSITORY_ROOT, mods_directory), mods_directory,
                               nodes=load_mod_tree_nodes(REPOSITORY_ROOT, mods_directory))


def trade_notes(registry: Mapping[str, Trade]) -> Dict[str, str]:
    """{trade id: the explanatory note of the trade}."""
    return {trade_id: trade.note for trade_id, trade in registry.items()}


def trades_absent(registry: Mapping[str, Trade]) -> FrozenSet[str]:
    """The trades that do not exist until someone teaches them."""
    return frozenset(trade_id for trade_id, trade in registry.items() if trade.initially_absent)


def trade_family(registry: Mapping[str, Trade], trade: str) -> str:
    """The family of `trade`; a trade the registry does not name is a craft."""
    record = registry.get(trade)
    return record.family if record is not None else DEFAULT_FAMILY
