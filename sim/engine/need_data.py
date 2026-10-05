"""Household needs and the goods that satisfy them, from data/world/needs.json and mods.

A need is a category households spend on. A good declares which needs it
satisfies and how well per unit. A mod adds needs (ids namespaced as
`<mod_id>:<name>`) and adds or extends goods; merging is additive.
"""
import os
from typing import Any, Dict, Optional

from sim.json_files import read_json

from .mods import ModError, get_ordered_mods
from .mods_base import deep_merge
from .mods_ids import check_new_id


def load_needs(root: str, mods_dir: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """{"needs": {...}, "goods": {...}}: base file, then each mod's, in dependency order."""
    mods_dir = mods_dir or os.path.join(root, "mods")
    needs: Dict[str, Any] = {}
    goods: Dict[str, Any] = {}

    def merge(path, manifest):
        if not os.path.isfile(path):
            return
        content = read_json(path)
        for need_id, spec in (content.get("needs") or {}).items():
            if need_id not in needs:
                if manifest:
                    check_new_id(manifest, need_id, False, path)
                needs[need_id] = {}
            needs[need_id] = deep_merge(needs[need_id], spec)
        for material, attributes in (content.get("goods") or {}).items():
            goods[material] = deep_merge(goods.get(material, {}), attributes)

    merge(os.path.join(root, "data", "world", "needs.json"), None)
    for manifest in get_ordered_mods(mods_dir):
        merge(os.path.join(manifest.directory, "data", "world", "needs.json"), manifest)
    check_needs(needs, goods)
    return {"needs": needs, "goods": goods}


def check_needs(needs: Dict[str, Any], goods: Dict[str, Any]) -> None:
    """Every good names known needs; every need has a positive budget weight."""
    for need_id, spec in needs.items():
        if not spec.get("surplus_budget_share", 0) > 0:
            raise ModError("need %r needs a positive surplus_budget_share" % need_id)
        if not spec.get("satiation_per_capita_per_year", 1) > 0:
            raise ModError("need %r needs a positive satiation_per_capita_per_year" % need_id)
    for material, attributes in goods.items():
        for need_id, effectiveness in (attributes.get("satisfies") or {}).items():
            if need_id not in needs:
                raise ModError("good %r satisfies unknown need %r" % (material, need_id))
            if not effectiveness > 0:
                raise ModError("good %r has non-positive effectiveness for %r"
                               % (material, need_id))
