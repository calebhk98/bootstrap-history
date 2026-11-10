"""Where numba keeps the compiled kernels: one directory per content of the source the kernels are compiled from.

numba's own cache checks only the file a kernel is defined in, so a caller compiled against a callee in another file keeps
the old callee's code after that file changes. The directory is named by a digest of the source, so an edit (or a branch
switch) compiles afresh instead of running stale code. `ROME_KERNEL_CACHE_KEY` picks what the digest covers:

- `source` (the default: games, the orchestrator, `--slow` runs and checks before a pull request): every `.py` under `sim/`
  but the tests, which also covers a constant a kernel reads from a file that defines no kernel (numba freezes globals at
  compile time). Any edit compiles every kernel again.
- `kernels` (the quick test tier unless set, and subagents' edit-test loops): only the files that mention `njit`, so an
  edit elsewhere keeps the compiled kernels. A changed constant in such a file is the one thing it can miss.

`NUMBA_CACHE_DIR` set by hand overrides all of this."""
import hashlib
import os
import shutil
from typing import List

from .cache_root import cache_directory

SIM_ROOT = os.path.dirname(os.path.abspath(__file__))
KEPT_DIRECTORIES = 4          # older directories are removed when a new one is made
SCOPE_ENV = "ROME_KERNEL_CACHE_KEY"
SCOPES = ("source", "kernels")
_MARKER = b"njit"


def scope() -> str:
    """What the key covers: `ROME_KERNEL_CACHE_KEY`, else `source`; an unknown value refuses."""
    named = os.environ.get(SCOPE_ENV) or "source"
    if named not in SCOPES:
        raise ValueError("%s must be one of %s, not %r" % (SCOPE_ENV, ", ".join(SCOPES), named))
    return named


def kernel_files(top: str = SIM_ROOT, covered: str = "kernels") -> List[str]:
    """The source files under `top` the key covers, tests left out, in a fixed order: those that mention `njit` for
    `kernels`, every `.py` for `source`."""
    found = []
    for directory, subdirectories, names in os.walk(top):
        subdirectories[:] = sorted(name for name in subdirectories if name not in ("tests", "__pycache__"))
        for name in sorted(names):
            if name.endswith(".py"):
                path = os.path.join(directory, name)
                with open(path, "rb") as handle:
                    if covered == "source" or _MARKER in handle.read():
                        found.append(path)
    return found


def kernel_source_key(top: str = SIM_ROOT, covered: str = "kernels") -> str:
    """A digest of the covered files' paths (relative to `top`) and contents."""
    digest = hashlib.sha256()
    for path in kernel_files(top, covered):
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
    """The directory for this source's compiled kernels under the chosen scope, made if new (old ones pruned)."""
    covered = scope()
    parent = cache_directory("numba")
    path = os.path.join(parent, "%s-%s" % (covered, kernel_source_key(covered=covered)))
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)
        prune(parent, path)
    os.utime(path)
    return path
