"""What finishing each technology does to the society: the base effects table with the mods' entries applied."""
import copy
import json
import os
from typing import Any, Dict

from sim.default_civilisation import CIVILISATION_DIRECTORY

from .directory_stamp import DirectoryMemo
from .mods import get_ordered_mods
from .mods_world import merge_mod_map

EFFECTS_FILE = os.path.join(CIVILISATION_DIRECTORY, "_TECH_EFFECTS.json")
_RELATIVE = "civilizations/_TECH_EFFECTS.json"


_remembered = DirectoryMemo()


def load_tech_effects(directory: str, path: str = EFFECTS_FILE) -> Dict[str, Any]:
    """{node id: its effects} from the file at `path` (keys starting with an underscore are notes) and the mods of `directory`.
    The shipped file is remembered per directory until a file under the directory changes; the caller gets its own copy."""
    if path != EFFECTS_FILE:
        return _built(directory, path)
    return copy.deepcopy(_remembered.get(directory, lambda: _built(directory, path)))


def _built(directory: str, path: str) -> Dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as source:
            effects = json.load(source)
        base = {key: value for key, value in effects.items() if not key.startswith("_")}
    except OSError:
        base = {}
    return merge_mod_map(base, get_ordered_mods(directory), _RELATIVE, None, "tech effect")
