"""Spun-up openings shipped with the checkout, so a player's first game skips the hidden spin-up years.

Each file is the record the spin-up writes to the disk cache, compressed, under the same cache key: the
opening's setup, the data files and the source the spin-up runs. A shipped record whose key no longer
matches (any change to that source or data) is never read; the game computes its own as before. The
`openings` subcommand writes them.
"""
import json
import lzma
import os
from typing import Any, Optional

from sim.cache_root import CHECKOUT_ROOT

SHIPPED_OPENINGS_DIRECTORY = os.path.join(CHECKOUT_ROOT, "openings")
SUFFIX = ".json.xz"


def path_of(key: str, directory: Optional[str] = None) -> str:
    return os.path.join(directory or SHIPPED_OPENINGS_DIRECTORY, key + SUFFIX)


def read(key: str, directory: Optional[str] = None) -> Optional[Any]:
    """The shipped record under `key`, or None when none is shipped."""
    try:
        with lzma.open(path_of(key, directory), "rt", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, lzma.LZMAError):
        return None


def write(key: str, record: Any, directory: Optional[str] = None) -> str:
    """Ship `record` under `key`; returns the file written."""
    path = path_of(key, directory)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with lzma.open(path, "wt", encoding="utf-8", preset=9) as handle:
        handle.write(json.dumps(record))
    return path


def shipped_keys(directory: Optional[str] = None):
    """The keys of every shipped record."""
    try:
        names = os.listdir(directory or SHIPPED_OPENINGS_DIRECTORY)
    except OSError:
        return []
    return sorted(name[:-len(SUFFIX)] for name in names if name.endswith(SUFFIX))
