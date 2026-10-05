"""Which civilisation to use when none is named: the preferred one, or the first civilisation
file present if that one is absent. Shared by the engine and the labour package's reference
figures, so neither imports the other."""
import functools
import os

REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CIVILISATION_DIRECTORY = os.path.join(REPOSITORY_ROOT, "data", "civilizations")
PREFERRED_DEFAULT_CIVILISATION = "rome_100ad"


def _file_ids():
    return sorted(name[:-5] for name in os.listdir(CIVILISATION_DIRECTORY)
                  if name.endswith(".json") and not name.startswith("_"))


@functools.lru_cache(maxsize=None)
def default_civilisation_id() -> str:
    present = _file_ids()
    if PREFERRED_DEFAULT_CIVILISATION in present or not present:
        return PREFERRED_DEFAULT_CIVILISATION
    return present[0]
