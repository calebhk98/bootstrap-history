"""Strategy files a mod ships in `data/strategies/`, named `<mod_id>:<name>` (written with `+` in the file name)."""
import os
from typing import Iterable, Optional

from .mods_base import ModManifest
from .mods_civ import civ_file_stem


def mod_strategy_path(name: str, manifests: Iterable[ModManifest]) -> Optional[str]:
    """The file of a mod strategy called `name`, or None. Only the owning mod's folder is searched."""
    owner = str(name).partition(":")[0]
    for manifest in manifests:
        if manifest.id == owner:
            path = os.path.join(manifest.directory, "data", "strategies", civ_file_stem(str(name)) + ".json")
            return path if os.path.isfile(path) else None
    return None


def mod_strategy_names(manifests: Iterable[ModManifest]) -> list:
    """Every `<mod_id>:<name>` strategy installed mods ship."""
    found = []
    for manifest in manifests:
        folder = os.path.join(manifest.directory, "data", "strategies")
        prefix = civ_file_stem(manifest.id) + "+"
        if os.path.isdir(folder):
            found.extend(filename[:-5].replace("+", ":") for filename in sorted(os.listdir(folder))
                         if filename.endswith(".json") and filename.startswith(prefix))
    return found
