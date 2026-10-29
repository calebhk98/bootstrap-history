"""What finishing each technology does to the society: the base effects table with the mods' entries applied."""
import json
import os
from typing import Any, Dict

from sim.default_civilisation import CIVILISATION_DIRECTORY

from .mods import get_ordered_mods
from .mods_world import merge_mod_map

EFFECTS_FILE = os.path.join(CIVILISATION_DIRECTORY, "_TECH_EFFECTS.json")
_RELATIVE = "civilizations/_TECH_EFFECTS.json"


def load_tech_effects(directory: str, path: str = EFFECTS_FILE) -> Dict[str, Any]:
    """{node id: its effects} from the file at `path` (keys starting with an underscore are notes) and the mods of `directory`."""
    try:
        with open(path, encoding="utf-8") as source:
            effects = json.load(source)
        base = {key: value for key, value in effects.items() if not key.startswith("_")}
    except OSError:
        base = {}
    return merge_mod_map(base, get_ordered_mods(directory), _RELATIVE, None, "tech effect")
