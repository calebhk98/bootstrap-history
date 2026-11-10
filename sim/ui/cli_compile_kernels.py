"""`compile-kernels`: compile every numba kernel the game uses, so the first game year in a fresh environment does not
spend a minute compiling (an environment's setup script runs this once; numba keeps the result in its cache directory,
`NUMBA_CACHE_DIR`, or the directory `sim/kernel_cache.py` keys on the kernel files' content).

Two sources: the small fixture economy is stepped a few years (it reaches nearly every kernel with the types a real
game passes), and `kernel_signatures.declared_signatures` names the types of the kernels it does not reach. A kernel
left with no compiled signature is listed and the command fails."""
import importlib
import os
import pkgutil
import sys
import time
import types

import sim
from sim import jit
from sim.ui.kernel_signatures import declared_signatures
from sim.ui.spin_up_fixture_trace import fixture_trace

FIXTURE_YEARS = 3


def import_kernel_modules():
    """Import every module under `sim` that compiles a kernel, so `jit.REGISTRY` is complete."""
    root = os.path.dirname(sim.__file__)
    for info in pkgutil.walk_packages([root], "sim."):
        if ".tests" in info.name or info.name.endswith("__main__"):
            continue
        path = os.path.join(root, *info.name.split(".")[1:]) + ".py"
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as handle:
            if "sim.jit import" in handle.read():
                importlib.import_module(info.name)


def kernel_name(kernel):
    return kernel.__module__ + "." + kernel.__name__


def called_kernels(kernel):
    """The registered kernels the kernel's code refers to, by name or as an attribute of an imported module (they
    compile with it, as numba compiles callees)."""
    function = kernel.py_func
    names = function.__code__.co_names
    named = [function.__globals__.get(name) for name in names]
    named += [getattr(module, name, None) for module in named if isinstance(module, types.ModuleType) for name in names]
    return [other for other in named if other is not kernel and any(other is entry for entry in jit.REGISTRY)]


def uncompiled(registry=None):
    """The names of registered kernels that neither have a compiled signature nor are called by one that is (a callee
    compiles with its caller, and a warm cache hands back only the caller's signature)."""
    registry = jit.REGISTRY if registry is None else registry
    reached = [kernel for kernel in registry if kernel.signatures]
    for kernel in reached:
        for callee in called_kernels(kernel):
            if callee not in reached:
                reached.append(callee)
    return sorted(kernel_name(kernel) for kernel in registry if kernel not in reached)


def compile_all():
    """Compile every registered kernel; (seconds, names of kernels still uncompiled)."""
    began = time.perf_counter()
    jit.load_numba()
    import_kernel_modules()
    fixture_trace("small", FIXTURE_YEARS)
    declared = declared_signatures()
    for kernel in jit.REGISTRY:
        for argument_types in declared.get(kernel_name(kernel), []):
            kernel.compile(argument_types)
    return time.perf_counter() - began, uncompiled()


def jobs_of(asked):
    """The processes to compile in: as asked, else the cores this process may use."""
    if asked:
        return max(1, asked)
    return len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else (os.cpu_count() or 1)


def cmd_compile_kernels(args):
    from . import compile_parallel
    internal = getattr(args, "internal", None)
    if internal:     # a step run in a child process by `compile_parallel`
        if internal[0] == compile_parallel.RECORD:
            compile_parallel.record_signatures(internal[1])
        else:
            compile_parallel.compile_share(internal[1], int(internal[2]))
        return
    if not jit.ENABLED:
        print("numba is not in use (not installed, or %s is set): nothing to compile" % jit.NO_JIT_ENV)
        return
    began = time.perf_counter()
    jobs = jobs_of(getattr(args, "jobs", 0))
    if jobs > 1:
        compile_parallel.compile_in_parallel(jobs)     # a worker that fails leaves its kernels to the serial pass below
    seconds, missing = compile_all()
    seconds = time.perf_counter() - began
    print("compiled %d kernels in %.1f s" % (len(jit.REGISTRY), seconds))
    if missing:
        print("kernels reached by neither the fixture nor kernel_signatures.py:\n  " + "\n  ".join(missing))
        sys.exit(1)
