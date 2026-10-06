"""Where the on-disk caches live. Every git worktree of a checkout shares the main checkout's `.cache/`,
and ROME_CACHE_DIR names one directory for separate clones. Cache keys hash content with paths relative
to the checkout, so sharing only ever returns what this checkout would compute itself."""
import os
from typing import Optional

CACHE_DIRECTORY_ENV = "ROME_CACHE_DIR"
CHECKOUT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _main_checkout(checkout: str) -> Optional[str]:
    """The main checkout a git worktree belongs to; None for a main checkout or anything unreadable.
    A worktree's `.git` is a file naming its record under the main `.git/worktrees/`."""
    try:
        with open(os.path.join(checkout, ".git"), encoding="utf-8") as handle:
            line = handle.read().strip()
        if not line.startswith("gitdir:"):
            return None
        record = os.path.normpath(os.path.join(checkout, line[len("gitdir:"):].strip()))
        with open(os.path.join(record, "commondir"), encoding="utf-8") as handle:
            common = os.path.normpath(os.path.join(record, handle.read().strip()))
    except OSError:  # a directory `.git` (a main checkout) or a record that is gone
        return None
    return os.path.dirname(common) if os.path.isdir(common) else None


def cache_root(checkout: str = CHECKOUT_ROOT) -> str:
    """The directory every cache of `checkout` lives under."""
    named = os.environ.get(CACHE_DIRECTORY_ENV)
    if named:
        return os.path.abspath(named)
    return os.path.join(_main_checkout(checkout) or checkout, ".cache")


def cache_directory(name: str) -> str:
    """The directory of one named cache."""
    return os.path.join(cache_root(), name)
