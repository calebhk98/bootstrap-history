"""The compiler every ported kernel goes through: numba's `njit` with the settings that keep a game reproducible, or the
plain function when numba is not installed or `ROME_NO_JIT` is set (slow, for debugging and for machines without numba).

Settings: nopython mode; no fastmath (no reassociation or fused multiply-add, so the same machine gives the same game);
no parallel loops (their thread order is not fixed); `cache=True`, so a kernel compiles once per machine and source and
later processes read the compiled code from a directory keyed on every kernel file's content (`sim/kernel_cache.py`).

numba itself is imported when the first kernel is called, not when a module defining one is imported: a command that
reaches no kernel never pays for it. Until then a kernel is a `LazyKernel`; the first call builds the real dispatcher of
every kernel defined so far and swaps them in for the stand-ins (module globals, registry), so kernels still call each
other.

A kernel takes and returns numpy arrays and numbers only. A phase packs its records into arrays when it starts and
unpacks the answer when it ends (docs/architecture/NUMBA_PORT_PLAN.md)."""
import importlib.util
import os
import sys
import types

NO_JIT_ENV = "ROME_NO_JIT"

ENABLED = not os.environ.get(NO_JIT_ENV) and importlib.util.find_spec("numba") is not None

# Every game kernel compiled through `njit`, in import order: the dispatcher (or the plain function without numba; a
# `LazyKernel` until numba is loaded). `sim/ui/cli_compile_kernels.py` walks it after `load_numba()`; tests' own helpers
# are left out.
REGISTRY = globals().get("REGISTRY", [])
_STATE = globals().get("_STATE", {"numba": None})      # survives a reload of this module
_LAZY = globals().get("_LAZY", [])                      # every stand-in made before numba loaded, tests' own included


def _record(kernel):
    if kernel.__module__.startswith("sim.") and not kernel.__module__.startswith("sim.tests"):
        REGISTRY.append(kernel)


def _settings(options):
    settings = {"cache": True, "fastmath": False, "parallel": False, "nogil": False}
    settings.update(options)
    return settings


class LazyKernel:
    """A kernel whose numba dispatcher is built on its first call (see the module docstring)."""

    def __init__(self, function, options):
        self.py_function = function
        self.options = options
        self.dispatcher = None
        self.__module__ = function.__module__
        self.__name__ = function.__name__
        self.__qualname__ = function.__qualname__
        self.__doc__ = function.__doc__

    def build(self):
        """The dispatcher (numba is imported and every other stand-in swapped out on the way)."""
        if self.dispatcher is None:
            numba = load_numba()
            if self.dispatcher is None:          # made after numba loaded
                self.dispatcher = numba.njit(**_settings(self.options))(self.py_function)
        return self.dispatcher

    def __call__(self, *arguments, **keywords):
        dispatcher = self.build() if self.dispatcher is None else self.dispatcher
        return dispatcher(*arguments, **keywords)

    def __getattr__(self, name):
        if name.startswith("__") or name in ("py_function", "options", "dispatcher"):
            raise AttributeError(name)
        return getattr(self.build() if self.dispatcher is None else self.dispatcher, name)


def load_numba():
    """Import numba and replace every `LazyKernel` by its dispatcher, in the registry and wherever a module holds one."""
    if _STATE["numba"] is not None:
        return _STATE["numba"]
    import numba
    if not os.environ.get("NUMBA_CACHE_DIR"):
        from .kernel_cache import kernel_cache_directory
        numba.config.CACHE_DIR = kernel_cache_directory()       # read when each dispatcher is made, so set before any
    _STATE["numba"] = numba
    for kernel in _LAZY:
        kernel.dispatcher = numba.njit(**_settings(kernel.options))(kernel.py_function)
    for index, kernel in enumerate(REGISTRY):
        if isinstance(kernel, LazyKernel):
            REGISTRY[index] = kernel.dispatcher
    for module in list(sys.modules.values()):
        namespace = getattr(module, "__dict__", None)
        if isinstance(module, types.ModuleType) and namespace:
            for name, value in list(namespace.items()):
                if isinstance(value, LazyKernel):
                    namespace[name] = value.dispatcher
    _LAZY.clear()
    return numba


def numba_loaded():
    """Whether the first kernel call (or `load_numba`) has already paid for importing numba."""
    return _STATE["numba"] is not None


def njit(function=None, **options):
    """`@njit` or `@njit(...)`: the function compiled with the reproducible settings, or unchanged without numba."""
    def wrap(inner):
        if not ENABLED:
            _record(inner)
            return inner
        if _STATE["numba"] is not None:
            compiled = _STATE["numba"].njit(**_settings(options))(inner)
        else:
            compiled = LazyKernel(inner, options)
            _LAZY.append(compiled)
        _record(compiled)
        return compiled
    return wrap if function is None else wrap(function)
