"""The engine services the price calculator still reaches: the production and tree loaders, the civilisation loader,
the shipped openings and the source closure. This is the package's only door to `sim.engine`; each service is imported
where it is called, so the package loads without the engine and the engine can import the package. A debt: it goes
when the data loaders have an owner of their own."""
from typing import Any, Dict, List, Optional


def load_production(mods_dir: Optional[str] = None) -> Any:
    from sim.engine.validate_production import load_production as loaded
    return loaded(mods_dir)


def load_mod_tree_nodes(root: str, mods_dir: Optional[str] = None) -> Any:
    from sim.content.api import load_mod_tree_nodes as loaded
    return loaded(root, mods_dir)


def load_trade_registry(root: str, production_entries: Any, nodes: Any = (), mods_dir: Optional[str] = None) -> Any:
    from sim.content.api import load_trade_registry as loaded
    return loaded(root, production_entries, mods_dir, nodes=nodes)


def closure(nodes: Dict[str, Any], node_id: str) -> Any:
    from sim.knowledge.api import closure as reached
    return reached(nodes, node_id)


def load_civ(civilization_id: Optional[str], mods_dir: Optional[str] = None) -> Any:
    from sim.engine.data import load_civ as loaded
    return loaded(civilization_id, mods_dir=mods_dir)


def shipped_opening(namespace: str, key: str) -> Any:
    """The entry shipped with the checkout under `key` in the cache `namespace`, or None."""
    from sim.engine import shipped_openings
    return shipped_openings.read(namespace, key)


def source_files(root: str, modules: Any, cache_directory: Optional[str] = None) -> List[str]:
    from sim.engine import source_closure
    return source_closure.source_files(root, modules, cache_directory=cache_directory)
