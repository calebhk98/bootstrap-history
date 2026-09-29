"""Canonical, mod-aware catalogues for production materials and trades.

This module is deliberately the only place which walks ``data/production``.
Consumers may still accept an explicit production mapping for small unit tests,
but their default view must come from here.
"""
import dataclasses
from dataclasses import dataclass
import json
import os
from typing import Any, Dict, Iterable, Mapping, Optional, Set, Tuple

from .mods import ModError, ModManifest, get_ordered_mods, load_mod_production, load_mod_tree
from .mods_ids import check_new_id, is_mod_content
from .mods_base import check_not_removed, claim_fields, claim_removal, deep_merge
from .mods_remove import RECIPE, TRADE, check_trade_references, scan_removed


@dataclass(frozen=True)
class Trade:
    id: str
    family: str = "craft"
    training: Optional[str] = None
    training_years: Optional[float] = None
    note: str = ""
    initially_absent: bool = False
    source: str = ""


def _trade_from(trade_id: str, metadata: Mapping[str, Any], source: str) -> Trade:
    return Trade(trade_id,
                 family=metadata.get("family", "craft"),
                 training=metadata.get("training"),
                 training_years=metadata.get("training_years"),
                 note=metadata.get("note", ""),
                 initially_absent=bool(metadata.get("initially_absent", False)),
                 source=source)


_production_cache: Dict[Tuple[str, str], Dict[str, Any]] = {}


def load_production_catalog(root: str, mods_dir: Optional[str] = None,
                            manifests: Optional[Iterable[ModManifest]] = None
                            ) -> Dict[str, Any]:
    """Load base recipes and enabled mods in deterministic dependency order."""
    mods_dir = mods_dir or os.path.join(root, "mods")
    cache_key = (os.path.abspath(root), os.path.abspath(mods_dir))
    if manifests is None and cache_key in _production_cache:
        return _production_cache[cache_key]
    merged: Dict[str, Any] = {}
    origins: Dict[str, str] = {}
    directory = os.path.join(root, "data", "production")
    if os.path.isdir(directory):
        for filename in sorted(os.listdir(directory)):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(directory, filename)
            with open(path, encoding="utf-8") as source:
                entries = (json.load(source).get("materials") or {})
            for material, entry in entries.items():
                if material in merged:
                    raise ModError("production id %s is defined in both %s and %s" %
                                   (material, origins[material], path))
                merged[material] = entry
                origins[material] = path
    ordered = list(manifests) if manifests is not None else get_ordered_mods(mods_dir)
    merged = load_mod_production(merged, ordered)
    if manifests is None:
        _production_cache[cache_key] = merged
    return merged


def material_namespace(production: Mapping[str, Any],
                       nodes: Iterable[Mapping[str, Any]] = ()) -> Set[str]:
    """All declared/referenced materials, independent of the old price book."""
    materials: Set[str] = set(production)
    for entry in production.values():
        materials.update((entry.get("outputs") or {}).keys())
        materials.update((entry.get("inputs") or {}).keys())
        for capital in entry.get("capital") or ():
            materials.update((capital.get("build_materials") or {}).keys())
    for node in nodes:
        materials.update((node.get("mat") or {}).keys())
    return materials


def validate_mod_material_paths(nodes: Iterable[Mapping[str, Any]],
                                production: Mapping[str, Any],
                                manifests: Iterable[ModManifest]) -> None:
    """Reject a mod technology reference for which no producer exists."""
    producers = set(production)
    for entry in production.values():
        producers.update((entry.get("outputs") or {}).keys())
    manifests = list(manifests)
    removed = scan_removed(manifests, RECIPE)
    for node in nodes:
        for material in (node.get("mat") or {}):
            if material in removed and material not in producers:
                raise ModError("technology %s references material %s; mod %s removed the "
                               "recipe that produced it" % (node.get("id"), material,
                                                            removed[material]))
    for node in nodes:
        node_id = str(node.get("id", ""))
        if not is_mod_content(node_id, manifests):
            continue
        for material in (node.get("mat") or {}):
            if material not in producers:
                raise ModError("mod technology %s references material %s, but no "
                               "production recipe produces that material" %
                               (node_id, material))


def load_mod_tree_nodes(root: str, mods_dir: Optional[str] = None) -> Iterable[Dict[str, Any]]:
    """Technology nodes of the base tree with enabled mods applied."""
    with open(os.path.join(root, "data", "tech_tree.json"), encoding="utf-8") as source:
        base_tree = json.load(source)
    tree = load_mod_tree(base_tree, get_ordered_mods(mods_dir or os.path.join(root, "mods")),
                         copy_base=False)
    return tree["nodes"]


def load_trade_registry(root: str, production: Optional[Mapping[str, Any]] = None,
                        mods_dir: Optional[str] = None,
                        nodes: Iterable[Mapping[str, Any]] = ()) -> Dict[str, Trade]:
    """Return trade identity/metadata without requiring a wage-table row.

    ``trade_families.json`` remains a supported shorthand.  Mods may instead
    use ``data/world/trades.json`` with a ``trades`` object whose values carry
    ``family`` and optional ``training`` and ``training_years`` metadata.
    """
    mods_dir = mods_dir or os.path.join(root, "mods")
    manifests = get_ordered_mods(mods_dir)
    registry: Dict[str, Trade] = {}
    claims: Dict[Any, str] = {}
    by_id = {manifest.id: manifest for manifest in manifests}

    def add_file(path: str, manifest: Optional[ModManifest]) -> None:
        if not os.path.isfile(path):
            return
        with open(path, encoding="utf-8") as source:
            raw = json.load(source)
        additions = dict(raw.get("trades") or {})
        additions.update({key: {"family": value} for key, value in
                          (raw.get("trade_families") or {}).items()})
        for trade_id, metadata in additions.items():
            if manifest and isinstance(metadata, dict) and metadata.get("remove") is True:
                if trade_id not in registry:
                    raise ModError("mod %s: %s removes missing trade %r" %
                                   (manifest.id, path, trade_id))
                claim_removal(claims, TRADE, trade_id, manifest, by_id)
                del registry[trade_id]
                continue
            if manifest and isinstance(metadata, dict) and metadata.get("override") is True:
                check_not_removed(claims, TRADE, trade_id, manifest, by_id)
                if trade_id not in registry:
                    raise ModError("mod %s: %s overrides missing trade %r" %
                                   (manifest.id, path, trade_id))
                claim_fields(claims, TRADE, trade_id, metadata, manifest, by_id)
                registry[trade_id] = _trade_from(trade_id, deep_merge(
                    dataclasses.asdict(registry[trade_id]), metadata), registry[trade_id].source)
                continue
            if manifest:
                check_new_id(manifest, trade_id, False, path)
            if trade_id in registry:
                raise ModError("trade %s is already defined before %s" % (trade_id, path))
            if isinstance(metadata, str):
                metadata = {"family": metadata}
            registry[trade_id] = _trade_from(trade_id, metadata, path)

    world = os.path.join(root, "data", "world")
    add_file(os.path.join(world, "trades.json"), None)
    add_file(os.path.join(world, "trade_families.json"), None)
    for manifest in manifests:
        world = os.path.join(manifest.directory, "data", "world")
        add_file(os.path.join(world, "trades.json"), manifest)
        add_file(os.path.join(world, "trade_families.json"), manifest)
    production = production or load_production_catalog(root, mods_dir)
    check_trade_references(registry, production, nodes, scan_removed(manifests, TRADE))
    for entry in production.values():
        for trade_id in (entry.get("labour_hours") or {}):
            registry.setdefault(trade_id, Trade(trade_id, source="production"))
        for capital in entry.get("capital") or ():
            for trade_id in (capital.get("build_labour_hours") or {}):
                registry.setdefault(trade_id, Trade(trade_id, source="production capital"))
    return registry


def reset_catalog_caches() -> None:
    _production_cache.clear()
