"""Actor kinds mods bring: declared in data/world/actor_kinds.json, or registered by consented mod code."""
from typing import Any, Dict, Optional

from sim.agents.api import register_declared_kinds

from .data import MODDIR, ROOT
from .mod_code import run_mod_code
from .mods import get_ordered_mods
from .mods_base import ModError
from .mods_world import merge_mod_map
from .need_data import load_needs

KINDS_PATH = "world/actor_kinds.json"
RATES = ("birth_rate", "death_rate", "famine_death_rate")
_REGISTERED: Dict[str, Any] = {}


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


def register_mod_actor_kinds(mods_dir: Optional[str] = None) -> None:
    """Register every mod kind once per mods directory: consented code first, then data declarations."""
    mods_dir = mods_dir or MODDIR
    if _REGISTERED.get("dir") == mods_dir:
        return
    run_mod_code(mods_dir)
    register_declared_kinds(load_kind_declarations(ROOT, mods_dir))
    _REGISTERED["dir"] = mods_dir
