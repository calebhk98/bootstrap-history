"""Which civilisation to use when none is named: the `default_civ` setting,
or the first civilisation file present if that one is absent."""
import functools
import os

from .settings import CONFIG_DEFAULTS

CIVILISATION_DIRECTORY = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "civilizations")


def _file_ids():
    return sorted(name[:-5] for name in os.listdir(CIVILISATION_DIRECTORY)
                  if name.endswith(".json") and not name.startswith("_"))


@functools.lru_cache(maxsize=None)
def default_civilisation_id() -> str:
    preferred = CONFIG_DEFAULTS["default_civ"]
    present = _file_ids()
    if preferred in present or not present:
        return preferred
    return present[0]
