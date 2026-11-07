"""Where the full-length first stage's trace is kept, and under what key: the spin-up writes it as its first stage
runs (spin_up_run.py), and the opening checks read it (sim/engine/opening_checks_run.py)."""
from sim import cache_root
from sim.prices.api import solve_cache

from .port_key import SPIN_UP_SOURCE_MODULES, spin_up_key
from .spin_up import SPIN_UP_MAXIMUM_YEARS

TRACE_CACHE_DIRECTORY = cache_root.cache_directory("opening_traces")


def trace_key_of_setup(setup) -> str:
    """The cache key of the first stage's trace on the opening `setup`: that of its spin-up, which covers the data and
    source, with the stage's full length."""
    return solve_cache.solve_key({"opening_trace": spin_up_key(setup), "years": int(SPIN_UP_MAXIMUM_YEARS)},
                                 source_modules=SPIN_UP_SOURCE_MODULES)


def keep_trace(setup, rows) -> None:
    """Keep `rows` as the full-length trace of `setup`'s first stage, unless one is kept already."""
    solve_cache.cached_json(trace_key_of_setup(setup), lambda: rows, cache_dir=TRACE_CACHE_DIRECTORY)
