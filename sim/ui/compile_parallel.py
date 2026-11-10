"""`compile-kernels --jobs N`: compile the kernels in N processes that share numba's cache.

The argument types come from one run of the small fixture with numba off (a fraction of a second): each call from
Python into a kernel is recorded as `numba.typeof` of its arguments; calls between kernels are not, since a callee
compiles with its caller. The declared signatures (`kernel_signatures.py`) are added. Workers then compile their share,
the largest kernels first, and the serial pass that follows reads the cache and lists any kernel still uncompiled.
A signature missed here costs only time: the kernel compiles when first called, as without this command."""
import inspect
import os
import pickle
import subprocess
import sys
import tempfile

from sim import jit

RECORD = "record"
WORKER = "worker"


def _wrapped_for_recording(function, name, seen, depth):
    import numba

    def recording(*arguments, **keywords):
        if depth[0] == 0 and not keywords:
            try:
                seen.setdefault(name, set()).add(tuple(numba.typeof(argument) for argument in arguments))
            except (TypeError, ValueError):     # a type numba cannot name is left to compile when first called
                pass
        depth[0] += 1
        try:
            return function(*arguments, **keywords)
        finally:
            depth[0] -= 1
    return recording


def record_signatures(path):
    """In a process with numba off: run the fixture with every kernel recording its argument types; write them to `path`."""
    from sim.ui import cli_compile_kernels
    from sim.ui.spin_up_fixture_trace import fixture_trace
    cli_compile_kernels.import_kernel_modules()
    seen, depth = {}, [0]
    by_identity = {id(kernel): (kernel, cli_compile_kernels.kernel_name(kernel)) for kernel in jit.REGISTRY}
    wrappers = {}
    for module in list(sys.modules.values()):
        namespace = getattr(module, "__dict__", None)
        if not namespace or not getattr(module, "__name__", "").startswith("sim."):
            continue
        for attribute, value in list(namespace.items()):
            if id(value) in by_identity and callable(value):
                kernel, name = by_identity[id(value)]
                if id(kernel) not in wrappers:
                    wrappers[id(kernel)] = _wrapped_for_recording(kernel, name, seen, depth)
                namespace[attribute] = wrappers[id(kernel)]
    fixture_trace("small", cli_compile_kernels.FIXTURE_YEARS)
    with open(path, "wb") as handle:
        pickle.dump({name: sorted(signatures, key=repr) for name, signatures in seen.items()}, handle)


def shares(signatures_by_name, sizes, jobs):
    """The (name, signature) pairs split into `jobs` lists, largest kernel first, each to the list with least work so far."""
    work = sorted(((sizes.get(name, 0), name, signature) for name, signatures in signatures_by_name.items()
                   for signature in signatures), key=lambda entry: (-entry[0], entry[1], repr(entry[2])))
    lists, loads = [[] for _ in range(jobs)], [0] * jobs
    for size, name, signature in work:
        lightest = loads.index(min(loads))
        lists[lightest].append((name, signature))
        loads[lightest] += max(size, 1)
    return lists


def compile_share(path, worker):
    """In a worker: compile the signatures of share `worker` written at `path`."""
    from sim.ui import cli_compile_kernels
    jit.load_numba()
    cli_compile_kernels.import_kernel_modules()
    by_name = {cli_compile_kernels.kernel_name(kernel): kernel for kernel in jit.REGISTRY}
    with open(path, "rb") as handle:
        share = pickle.load(handle)[worker]
    for name, signature in share:
        if name in by_name:
            by_name[name].compile(signature)


def _source_size(kernel):
    try:
        return len(inspect.getsource(getattr(kernel, "py_func", kernel)))
    except (OSError, TypeError):
        return 0


def compile_in_parallel(jobs):
    """Record the signatures, merge the declared ones, compile them in `jobs` processes; the workers' exit codes."""
    from sim.ui import cli_compile_kernels
    from sim.ui.kernel_signatures import declared_signatures
    script = os.path.abspath(sys.argv[0])
    with tempfile.TemporaryDirectory() as directory:
        recorded = os.path.join(directory, "recorded.pickle")
        subprocess.run([sys.executable, script, "compile-kernels", "--internal", RECORD, recorded],
                       env=dict(os.environ, **{jit.NO_JIT_ENV: "1"}), check=True)
        with open(recorded, "rb") as handle:
            signatures = {name: list(found) for name, found in pickle.load(handle).items()}
        jit.load_numba()
        cli_compile_kernels.import_kernel_modules()
        for name, declared in declared_signatures().items():
            signatures.setdefault(name, []).extend(tuple(signature) for signature in declared)
        sizes = {cli_compile_kernels.kernel_name(kernel): _source_size(kernel) for kernel in jit.REGISTRY}
        planned = os.path.join(directory, "shares.pickle")
        with open(planned, "wb") as handle:
            pickle.dump(shares(signatures, sizes, jobs), handle)
        workers = [subprocess.Popen([sys.executable, script, "compile-kernels", "--internal", WORKER, planned, str(worker)])
                   for worker in range(jobs)]
        return [worker.wait() for worker in workers]
