"""Persistent on-disk cache for price-solver results.

The key hashes every input that can change a solve: the production
catalogue in memory, the held gate nodes, the civilisation, the wage
ratios, the trade wage table, and the content of every file under `data/`
and `mods/` plus the solver's own source. Any change to an input gives a new
key, so a stale entry is never read. The cache is optional: a missing or
unreadable entry is a miss, and a failed write is ignored.
"""
import hashlib
import json
import os
import tempfile
from typing import Any, Callable, Dict, Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_CACHE_DIRECTORY = os.path.join(_ROOT, ".cache", "price_solves")
_DIGEST_LENGTH = 32
_DATA_SUFFIXES = (".json", ".md", ".txt", ".csv")

_environment_digest: Optional[str] = None


def _digest_tree(digest: Any, top: str, suffixes: tuple, skip_directories: tuple = ()) -> None:
    for directory, subdirectories, filenames in os.walk(top):
        subdirectories[:] = sorted(name for name in subdirectories
                                   if name not in skip_directories and name != "__pycache__")
        for filename in sorted(filenames):
            if not filename.endswith(suffixes):
                continue
            path = os.path.join(directory, filename)
            digest.update(os.path.relpath(path, _ROOT).encode("utf-8"))
            with open(path, "rb") as handle:
                digest.update(hashlib.sha256(handle.read()).digest())


def environment_digest() -> str:
    """Digest of the data files and solver source; computed once per process."""
    global _environment_digest
    if _environment_digest is None:
        digest = hashlib.sha256()
        _digest_tree(digest, os.path.join(_ROOT, "data"), _DATA_SUFFIXES)
        _digest_tree(digest, os.path.join(_ROOT, "mods"), _DATA_SUFFIXES)
        _digest_tree(digest, os.path.join(_ROOT, "sim"), (".py",), skip_directories=("tests",))
        _environment_digest = digest.hexdigest()
    return _environment_digest


def forget_environment_digest() -> None:
    global _environment_digest
    _environment_digest = None


def solve_key(inputs: Dict[str, Any]) -> str:
    """Hash of the in-memory solve inputs together with the environment digest."""
    payload = json.dumps({"inputs": inputs, "environment": environment_digest()},
                         sort_keys=True, default=lambda value: sorted(value))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:_DIGEST_LENGTH]


def cached_json(key: str, compute: Callable[[], Any],
                cache_dir: Optional[str] = None) -> Any:
    """The JSON-able value stored under `key`, computing and storing it on a miss."""
    directory = cache_dir or DEFAULT_CACHE_DIRECTORY
    path = os.path.join(directory, key + ".json")
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        pass
    text = json.dumps(compute())
    try:
        os.makedirs(directory, exist_ok=True)
        handle_fd, temporary = tempfile.mkstemp(dir=directory, suffix=".tmp")
        with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temporary, path)
    except OSError:
        pass
    # Cold and warm calls both return the parsed text, so they are identical.
    return json.loads(text)
