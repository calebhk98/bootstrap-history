"""Canonical, mod-aware catalogues for production materials and trades.

This module is deliberately the only place which walks ``data/production``.
Consumers may still accept an explicit production mapping for small unit tests,
but their default view must come from here.
"""
from dataclasses import dataclass
import json
import os
from typing import Any, Dict, Iterable, Mapping, Optional, Set, Tuple

from .mods import ModError, ModManifest, get_ordered_mods, load_mod_production


@dataclass(frozen=True)
class Trade:
    id: str
    family: str = "craft"
    training: Optional[str] = None
    source: str = ""


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
    prefixes = tuple(manifest.id + "_" for manifest in manifests)
    for node in nodes:
        node_id = str(node.get("id", ""))
        if not node_id.startswith(prefixes):
            continue
        for material in (node.get("mat") or {}):
            if material not in producers:
                raise ModError("mod technology %s references material %s, but no "
                               "production recipe produces that material" %
                               (node_id, material))


def load_trade_registry(root: str, production: Optional[Mapping[str, Any]] = None,
                        mods_dir: Optional[str] = None) -> Dict[str, Trade]:
    """Return trade identity/metadata without requiring a wage-table row.

    ``trade_families.json`` remains a supported shorthand.  Mods may instead
    use ``data/world/trades.json`` with a ``trades`` object whose values carry
    ``family`` and optional ``training`` metadata.
    """
    mods_dir = mods_dir or os.path.join(root, "mods")
    manifests = get_ordered_mods(mods_dir)
    registry: Dict[str, Trade] = {}

    def add_file(path: str, manifest: Optional[ModManifest]) -> None:
        if not os.path.isfile(path):
            return
        with open(path, encoding="utf-8") as source:
            raw = json.load(source)
        additions = dict(raw.get("trades") or {})
        additions.update({key: {"family": value} for key, value in
                          (raw.get("trade_families") or {}).items()})
        for trade_id, metadata in additions.items():
            if manifest and not trade_id.startswith(manifest.id + "_"):
                raise ModError("%s introduces un-prefixed trade id %r" % (path, trade_id))
            if trade_id in registry:
                raise ModError("trade %s is already defined before %s" % (trade_id, path))
            if isinstance(metadata, str):
                metadata = {"family": metadata}
            registry[trade_id] = Trade(trade_id, metadata.get("family", "craft"),
                                       metadata.get("training"), path)

    world = os.path.join(root, "data", "world")
    add_file(os.path.join(world, "trades.json"), None)
    add_file(os.path.join(world, "trade_families.json"), None)
    for manifest in manifests:
        world = os.path.join(manifest.directory, "data", "world")
        add_file(os.path.join(world, "trades.json"), manifest)
        add_file(os.path.join(world, "trade_families.json"), manifest)
    for entry in (production or load_production_catalog(root, mods_dir)).values():
        for trade_id in (entry.get("labour_hours") or {}):
            registry.setdefault(trade_id, Trade(trade_id, source="production"))
        for capital in entry.get("capital") or ():
            for trade_id in (capital.get("build_labour_hours") or {}):
                registry.setdefault(trade_id, Trade(trade_id, source="production capital"))
    return registry


def transitional_wage_rates(registry: Mapping[str, Trade],
                            calibrated: Mapping[str, float]) -> Dict[str, float]:
    """Inject wages for registered trades while equilibrium wages evolve.

    Calibrated rates are economic state, not identity.  Uncalibrated trades
    receive their family's median solely as a documented compatibility bridge.
    """
    rates = dict(calibrated)
    for trade_id, trade in registry.items():
        if trade_id in rates:
            continue
        family_rates = [rate for known, rate in rates.items()
                        if registry.get(known, Trade(known)).family == trade.family]
        rates[trade_id] = (sorted(family_rates)[len(family_rates) // 2]
                           if family_rates else rates.get("labourer", 0.05))
    return rates


def reset_catalog_caches() -> None:
    _production_cache.clear()
