"""A cheap fingerprint of a mods directory, so a table built from it is remembered until a file in it changes."""
import os
from typing import Callable, Dict, Tuple, TypeVar

Stamp = Tuple[Tuple[str, int, int], ...]
Table = TypeVar("Table")


def stamp_of(directory: str) -> Stamp:
    """(relative path, modification time, size) of every file under `directory`, sorted; a missing directory has an empty stamp."""
    entries = []
    for current, subdirectories, filenames in os.walk(directory):
        subdirectories[:] = sorted(name for name in subdirectories if name != "__pycache__")
        for filename in filenames:
            path = os.path.join(current, filename)
            try:
                status = os.stat(path)
            except OSError:
                continue
            entries.append((os.path.relpath(path, directory), status.st_mtime_ns, status.st_size))
    return tuple(sorted(entries))


class DirectoryMemo:
    """Remembers one table per mods directory path; a changed file under the directory builds it afresh."""

    def __init__(self) -> None:
        self._held: Dict[str, Tuple[Stamp, object]] = {}

    def get(self, directory: str, build: Callable[[], Table]) -> Table:
        stamp = stamp_of(directory)
        held = self._held.get(directory)
        if held is not None and held[0] == stamp:
            return held[1]  # type: ignore[return-value]
        table = build()
        self._held[directory] = (stamp, table)
        return table
