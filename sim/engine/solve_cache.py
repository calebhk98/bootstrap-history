"""Persistent on-disk cache for price-solver results.

The key hashes every input that can change a solve: the production
catalogue in memory, the held gate nodes, the civilisation, the wage
ratios, the trade wage table, and the content of every file under `data/`
and `mods/` plus the source the solver can import. Any change to an input gives a new
key, so a stale entry is never read. The cache is optional: a missing or
unreadable entry is a miss, and a failed write is ignored.
"""
import contextlib
import hashlib
import json
import os
import tempfile
from typing import Any, Callable, Dict, Iterator, Optional, Tuple

from sim import cache_root
from sim.engine import source_closure

try:
    import fcntl
except ImportError:  # Windows: misses are not coordinated
    fcntl = None

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_CACHE_DIRECTORY = cache_root.cache_directory("price_solves")
_DIGEST_LENGTH = 32
_DATA_SUFFIXES = (".json", ".md", ".txt", ".csv")

_environment_digests: Dict[Optional[Tuple[str, ...]], str] = {}


def _digest_tree(digest: Any, top: str, suffixes: tuple, skip_directories: tuple = ()) -> None:
    for directory, subdirectories, filenames in os.walk(top, followlinks=True):
        subdirectories[:] = sorted(name for name in subdirectories
                                   if name not in skip_directories and name != "__pycache__")
        for filename in sorted(filenames):
            if not filename.endswith(suffixes):
                continue
            _digest_file(digest, os.path.join(directory, filename))


def _digest_file(digest: Any, path: str) -> None:
    digest.update(os.path.relpath(path, _ROOT).encode("utf-8"))
    with open(path, "rb") as handle:
        digest.update(hashlib.sha256(handle.read()).digest())


def environment_digest(source_modules: Optional[Tuple[str, ...]] = None) -> str:
    """Digest of the data files and the source; computed once per process for each scope.

    With `source_modules`, only the sim source those modules can import is hashed, so editing
    code they never reach keeps the cache; without, every .py under sim/ is."""
    if source_modules not in _environment_digests:
        digest = hashlib.sha256()
        _digest_tree(digest, os.path.join(_ROOT, "data"), _DATA_SUFFIXES)
        _digest_tree(digest, os.path.join(_ROOT, "mods"), _DATA_SUFFIXES)
        if source_modules is None:
            _digest_tree(digest, os.path.join(_ROOT, "sim"), (".py",), skip_directories=("tests",))
        else:
            closure_cache = os.path.join(os.path.dirname(DEFAULT_CACHE_DIRECTORY), "source_closure")
            for path in source_closure.source_files(_ROOT, source_modules, cache_directory=closure_cache):
                _digest_file(digest, path)
        _environment_digests[source_modules] = digest.hexdigest()
    return _environment_digests[source_modules]


def forget_environment_digest() -> None:
    _environment_digests.clear()


def solve_key(inputs: Dict[str, Any], source_modules: Optional[Tuple[str, ...]] = None) -> str:
    """Hash of the in-memory solve inputs together with the environment digest."""
    payload = json.dumps({"inputs": inputs, "environment": environment_digest(source_modules)},
                         sort_keys=True, default=lambda value: sorted(value))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:_DIGEST_LENGTH]


def cached_json(key: str, compute: Callable[[], Any],
                cache_dir: Optional[str] = None) -> Any:
    """The JSON-able value stored under `key`, computing and storing it on a miss.

    A miss holds a per-key lock while it computes, so processes missing the same key at once
    (parallel test workers on a cold cache) wait for one computation and read its result."""
    directory = cache_dir or DEFAULT_CACHE_DIRECTORY
    path = os.path.join(directory, key + ".json")
    stored = _read(path)
    if stored is not None:
        return stored
    with _key_lock(directory, key):
        stored = _read(path)
        if stored is not None:
            return stored
        text = json.dumps(compute())
        try:
            handle_fd, temporary = tempfile.mkstemp(dir=directory, suffix=".tmp")
            with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
                handle.write(text)
            os.replace(temporary, path)
        except OSError:
            pass
    # Cold and warm calls both return the parsed text, so they are identical.
    return json.loads(text)


def _read(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


@contextlib.contextmanager
def _key_lock(directory: str, key: str) -> Iterator[None]:
    """An exclusive lock on one key across processes; no lock where the platform or directory gives none."""
    try:
        os.makedirs(directory, exist_ok=True)
        handle = open(os.path.join(directory, key + ".lock"), "a")
    except OSError:
        handle = None
    try:
        if handle is not None and fcntl is not None:
            fcntl.flock(handle, fcntl.LOCK_EX)
        yield
    finally:
        if handle is not None:
            handle.close()
