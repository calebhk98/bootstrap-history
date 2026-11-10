"""Which shipped openings still match the code: `openings/manifest.json` holds, for each civilisation, the digest of the
data files and spin-up source its opening was built from (`solve_cache.environment_digest` over the spin-up's source
scope, the part of every spin-up key that is not the civilisation's own setup, which follows from the same data and
source). A civilisation whose digest differs, or which has none, has a stale opening: a fresh environment would spin
it up from scratch. `openings` records each civilisation it ships; `tools/check_openings_current.py` lists the stale."""
import json
import os
from typing import Callable, Dict, Iterable, List

from sim.engine.shipped_openings import SHIPPED_OPENINGS_DIRECTORY

MANIFEST_PATH = os.path.join(SHIPPED_OPENINGS_DIRECTORY, "manifest.json")


def current_digest() -> str:
    """The digest a spin-up key covers besides the setup, for the code and data as they are now."""
    from sim.markets.port_key import SPIN_UP_SOURCE_MODULES
    from sim.prices.solve_cache import environment_digest
    return environment_digest(SPIN_UP_SOURCE_MODULES)


def read_manifest(path: str = MANIFEST_PATH) -> Dict[str, str]:
    try:
        with open(path, encoding="utf-8") as handle:
            return dict(json.load(handle))
    except (OSError, ValueError):
        return {}


def record(civ_ids: Iterable[str], digest: str, path: str = MANIFEST_PATH) -> None:
    """Note that these civilisations' openings were built from `digest`; the others keep what they had."""
    manifest = read_manifest(path)
    manifest.update({civ_id: digest for civ_id in civ_ids})
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(dict(sorted(manifest.items())), handle, indent=1)
        handle.write("\n")


def stale_civs(civ_ids: Iterable[str], digest_now: Callable[[], str] = current_digest, path: str = MANIFEST_PATH) -> List[str]:
    """The civilisations whose shipped opening was not built from the code and data as they are now."""
    manifest = read_manifest(path)
    now = digest_now()
    return [civ_id for civ_id in civ_ids if manifest.get(civ_id) != now]
