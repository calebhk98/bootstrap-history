"""Cache entries shipped with the checkout, so a player's first game skips the opening's hidden spin-up
and price solves.

Each file is an entry of a disk cache (solve_cache.cached_json), compressed, under the same key and in a
directory named like the cache's own: the key covers the inputs, the data files and the source, so an
entry whose code or data has changed since it was shipped is never read and the game computes its own
as before. The `openings` subcommand writes them.
"""
import json
import lzma
import os
from typing import Any, List, Optional, Tuple

from sim.cache_root import CHECKOUT_ROOT

SHIPPED_OPENINGS_DIRECTORY = os.path.join(CHECKOUT_ROOT, "openings")
SUFFIX = ".json.xz"


def path_of(namespace: str, key: str) -> str:
    return os.path.join(SHIPPED_OPENINGS_DIRECTORY, namespace, key + SUFFIX)


def read(namespace: str, key: str) -> Optional[Any]:
    """The shipped entry under `key` in the cache named `namespace`, or None when none is shipped."""
    try:
        with lzma.open(path_of(namespace, key), "rt", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, lzma.LZMAError):
        return None


def write(namespace: str, key: str, value: Any) -> str:
    """Ship `value` under `key`; returns the file written."""
    path = path_of(namespace, key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with lzma.open(path, "wt", encoding="utf-8", preset=9) as handle:
        handle.write(json.dumps(value))
    return path


def shipped_entries() -> List[Tuple[str, str]]:
    """(namespace, key) of every shipped entry."""
    entries = []
    try:
        namespaces = sorted(os.listdir(SHIPPED_OPENINGS_DIRECTORY))
    except OSError:
        return []
    for namespace in namespaces:
        directory = os.path.join(SHIPPED_OPENINGS_DIRECTORY, namespace)
        if os.path.isdir(directory):
            entries.extend((namespace, name[:-len(SUFFIX)]) for name in sorted(os.listdir(directory))
                           if name.endswith(SUFFIX))
    return entries
