"""Where numba keeps the compiled kernels: one directory per content of the files that define kernels.

numba's own cache checks only the file a kernel is defined in, so a caller compiled against a callee in another file keeps
the old callee's code after that file changes. Keying the directory on every kernel file's content means an edit to any
of them (or a branch switch) compiles afresh instead of running stale code. Not covered: a constant a kernel reads from a
file that defines no kernel (numba freezes globals at compile time); `NUMBA_CACHE_DIR` set by hand overrides all of this."""
import hashlib
import os
import shutil
from typing import List

from .cache_root import cache_directory

SIM_ROOT = os.path.dirname(os.path.abspath(__file__))
KEPT_DIRECTORIES = 4          # older directories are removed when a new one is made
_MARKER = b"njit"


def kernel_files(top: str = SIM_ROOT) -> List[str]:
    """Every source file under `top` that mentions `njit`, tests left out, in a fixed order."""
    found = []
    for directory, subdirectories, names in os.walk(top):
        subdirectories[:] = sorted(name for name in subdirectories if name not in ("tests", "__pycache__"))
        for name in sorted(names):
            if name.endswith(".py"):
                path = os.path.join(directory, name)
                with open(path, "rb") as handle:
                    if _MARKER in handle.read():
                        found.append(path)
    return found


def kernel_source_key(top: str = SIM_ROOT) -> str:
    """A digest of the kernel files' paths (relative to `top`) and contents."""
    digest = hashlib.sha256()
    for path in kernel_files(top):
        digest.update(os.path.relpath(path, top).encode("utf-8"))
        with open(path, "rb") as handle:
            digest.update(hashlib.sha256(handle.read()).digest())
    return digest.hexdigest()[:16]


def prune(parent: str, keep: str, kept: int = KEPT_DIRECTORIES) -> None:
    """Remove all but the `kept` most recently used directories under `parent`, never `keep`."""
    try:
        entries = [os.path.join(parent, name) for name in os.listdir(parent)]
    except OSError:
        return
    directories = sorted((path for path in entries if os.path.isdir(path) and path != keep), key=os.path.getmtime, reverse=True)
    for path in directories[max(0, kept - 1):]:
        shutil.rmtree(path, ignore_errors=True)


def kernel_cache_directory() -> str:
    """The directory for this source's compiled kernels, made if new (old ones pruned)."""
    parent = cache_directory("numba")
    path = os.path.join(parent, kernel_source_key())
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)
        prune(parent, path)
    os.utime(path)
    return path
