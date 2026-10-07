"""The base technology tree, built from the branch files at load time.

`data/branches/` is the only source. The tree is a pure function of the
branch files, the production catalogue and trade registry the merge checks
them against, and the merge code, so a cache keyed on the content of all of
those can never be stale. Nothing in the repository holds a copy of the result.
"""
import hashlib
import json
import os
import tempfile
from typing import Any, Dict, Iterator, Optional

from sim import cache_root

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_CACHE_DIRECTORY = cache_root.cache_directory("tech_tree")

META_FILE = "_META.json"
MERGED_DUPLICATE_IDS_FILE = "_MERGED_DUPLICATE_IDS.json"
# The base tree is checked against base data only; mods apply on top of it afterwards.
NO_MODS_DIRECTORY = os.path.join(ROOT, "data", "_no_mods")

_CODE_FILES = (("sim", "engine", "tree_merge.py"), ("sim", "engine", "tree_source.py"),
               ("sim", "engine", "catalog.py"))
_DATA_DIRECTORIES = (("data", "production"),)
_DATA_FILES = (("data", "world", "trades.json"), ("data", "world", "trade_families.json"))

_text_by_digest: Dict[str, str] = {}


def _branch_directory() -> str:
    from sim.engine import tree_merge
    return tree_merge.BR


def _input_paths(branch_directory: str) -> Iterator[str]:
    for directory in [branch_directory] + [os.path.join(ROOT, *parts) for parts in _DATA_DIRECTORIES]:
        if os.path.isdir(directory):
            for filename in sorted(os.listdir(directory)):
                if filename.endswith(".json"):
                    yield os.path.join(directory, filename)
    for parts in _DATA_FILES + _CODE_FILES:
        yield os.path.join(ROOT, *parts)


def input_digest(branch_directory: Optional[str] = None) -> str:
    """Digest of every file the build reads; any edit to one gives a new digest."""
    digest = hashlib.sha256()
    for path in _input_paths(branch_directory or _branch_directory()):
        try:
            with open(path, "rb") as handle:
                content = handle.read()
        except OSError:
            continue
        digest.update(os.path.basename(path).encode("utf-8"))
        digest.update(hashlib.sha256(content).digest())
    return digest.hexdigest()


def _read_cached(path: str) -> Optional[str]:
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return None


def _write_cached(directory: str, key: str, text: str) -> None:
    try:
        os.makedirs(directory, exist_ok=True)
        handle_fd, temporary = tempfile.mkstemp(dir=directory, suffix=".tmp")
        with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temporary, os.path.join(directory, key + ".json"))
        for filename in os.listdir(directory):
            if filename.endswith(".json") and filename != key + ".json":
                os.remove(os.path.join(directory, filename))
    except OSError:
        pass


def _build_text() -> str:
    from sim.engine import tree_merge
    built = tree_merge.build_tree()
    if built.collisions:
        raise ValueError("branch files define an id more than once: " + "; ".join(built.collisions))
    return json.dumps(built.tree)


def load_base_tree(cache_directory: Optional[str] = DEFAULT_CACHE_DIRECTORY) -> Dict[str, Any]:
    """The merged tree of the branch files, with no mods applied.

    Each call returns a fresh object the caller may mutate. A build is kept in
    memory for the process and, unless `cache_directory` is None, on disk
    under the digest of its inputs.
    """
    key = input_digest()
    text = _text_by_digest.get(key)
    if text is None and cache_directory:
        text = _read_cached(os.path.join(cache_directory, key + ".json"))
    if text is not None:
        try:
            tree = json.loads(text)
        except ValueError:
            text = None
    if text is None:
        text = _build_text()
        if cache_directory:
            _write_cached(cache_directory, key, text)
        tree = json.loads(text)
    _text_by_digest.clear()
    _text_by_digest[key] = text
    return tree
