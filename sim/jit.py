"""The compiler every ported kernel goes through: numba's `njit` with the settings that keep a game reproducible, or the
plain function when numba is not installed or `ROME_NO_JIT` is set (slow, for debugging and for machines without numba).

Settings: nopython mode; no fastmath (no reassociation or fused multiply-add, so the same machine gives the same game);
no parallel loops (their thread order is not fixed); `cache=True`, so a kernel compiles once per machine and source and
later processes read the compiled code from `__pycache__`.

A kernel takes and returns numpy arrays and numbers only. A phase packs its records into arrays when it starts and
unpacks the answer when it ends (docs/architecture/NUMBA_PORT_PLAN.md)."""
import os

NO_JIT_ENV = "ROME_NO_JIT"

try:
    if os.environ.get(NO_JIT_ENV):
        raise ImportError(NO_JIT_ENV)
    import numba as _numba
except ImportError:
    _numba = None

ENABLED = _numba is not None

# Every game kernel compiled through `njit`, in import order: the dispatcher (or the plain function without numba).
# `sim/ui/cli_compile_kernels.py` walks it; tests' own helpers are left out.
REGISTRY = globals().get("REGISTRY", [])


def _record(kernel):
    if kernel.__module__.startswith("sim.") and not kernel.__module__.startswith("sim.tests"):
        REGISTRY.append(kernel)


def njit(function=None, **options):
    """`@njit` or `@njit(...)`: the function compiled with the reproducible settings, or unchanged without numba."""
    def wrap(inner):
        if _numba is None:
            _record(inner)
            return inner
        settings = {"cache": True, "fastmath": False, "parallel": False, "nogil": False}
        settings.update(options)
        compiled = _numba.njit(**settings)(inner)
        _record(compiled)
        return compiled
    return wrap if function is None else wrap(function)
