"""A game process on a cold kernel cache compiles every kernel on all cores before it starts, instead of one kernel at a
time on one core as the game first reaches each (`compile_parallel.py`). Once per environment and source: a cache that
holds any compiled kernel is left as it is. Messages go to stderr; stdout is the game's protocol.
`ROME_COLD_COMPILE=0` turns it off."""
import os
import sys

from sim import jit
from . import compile_parallel
from .cli_compile_kernels import jobs_of

SWITCH_ENV = "ROME_COLD_COMPILE"


def cache_holds_kernels(directory: str) -> bool:
    """Whether numba's cache directory already holds a compiled kernel's index."""
    for _root, _directories, names in os.walk(directory):
        if any(name.endswith(".nbi") for name in names):
            return True
    return False


def kernel_directory() -> str:
    """The cache directory numba will use, found as `jit.load_numba` finds it, without importing numba."""
    if os.environ.get("NUMBA_CACHE_DIR"):
        return os.environ["NUMBA_CACHE_DIR"]
    from sim.kernel_cache import kernel_cache_directory
    return kernel_cache_directory()


def compile_if_cold() -> bool:
    """Compile every kernel in parallel when numba is in use, the switch is on, there are cores to share and the cache is
    empty; whether it did."""
    if not jit.ENABLED or os.environ.get(SWITCH_ENV, "1") == "0":
        return False
    jobs = jobs_of(0)
    if jobs < 2:
        return False
    if cache_holds_kernels(kernel_directory()):
        return False
    sys.stderr.write("compiling the game's kernels on %d cores (once per environment)...\n" % jobs)
    sys.stderr.flush()
    compile_parallel.compile_in_parallel(jobs)
    return True
