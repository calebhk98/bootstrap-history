"""Actor kinds mods declare in data/world/actor_kinds.json (a mod's code adds kinds through `api.actor_kind`)."""
import os
from typing import Any, Dict

from sim.agents.api import declared_kind_classes
from sim.default_civilisation import REPOSITORY_ROOT as ROOT

from .mods import get_ordered_mods
from .mods_base import ModError
from .mods_world import merge_mod_map
from .need_data import load_needs

MODDIR = os.path.join(ROOT, "mods")

KINDS_PATH = "world/actor_kinds.json"
RATES = ("birth_rate", "death_rate", "famine_death_rate")
_CLASSES: Dict[str, Dict[str, Any]] = {}   # mods directory -> {kind id: class}: data read once, the classes made once


def load_kind_declarations(root: str = ROOT, mods_dir: str = MODDIR) -> Dict[str, Dict[str, Any]]:
    """{kind id: declaration} from every installed mod, checked against the needs catalogue."""
    kinds = merge_mod_map({}, get_ordered_mods(mods_dir), KINDS_PATH, "kinds", "actor kind")
    needs = load_needs(root, mods_dir)["needs"]
    for kind, declaration in kinds.items():
        for rate in RATES:
            if not isinstance(declaration.get(rate), (int, float)) or isinstance(declaration.get(rate), bool):
                raise ModError("actor kind %s needs a numeric %s" % (kind, rate))
        declared = declaration.get("needs")
        if not isinstance(declared, dict) or not declared:
            raise ModError("actor kind %s needs 'needs', a map of need id to floor multiple" % kind)
        for need_id in list(declared) + list(declaration.get("vital_needs") or ()):
            if need_id not in needs:
                raise ModError("actor kind %s names unknown need %r" % (kind, need_id))
    return kinds


def declared_kinds(mods_dir: str = MODDIR) -> Dict[str, Any]:
    """{kind id: the class that builds its actors} for the kinds the mods of `mods_dir` declare, made once per directory."""
    if mods_dir not in _CLASSES:
        _CLASSES[mods_dir] = declared_kind_classes(load_kind_declarations(ROOT, mods_dir))
    return _CLASSES[mods_dir]
