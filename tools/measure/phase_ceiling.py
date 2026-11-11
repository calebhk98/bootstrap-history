"""Python time per phase of a warm year, by perf_counter: the most a rewrite of each phase into kernels can save.

    python3 tools/measure/phase_ceiling.py SAVE [--repeat N]

Times every year phase (`sim/engine/year_phases.py`) and every call the economy's year makes directly
(`Economy._run_year`, found from its source), and the time spent inside compiled kernels within each. A phase's Python
time is its wall time less its kernel time. Unlike cProfile this adds only a timer per phase and per call from Python into a kernel (the
number of kernel calls is printed, so their timer cost can be judged). The save is read, never written."""
import ast
import inspect
import sys
import textwrap
import time

sys.path.insert(0, ".")
from numba.core.registry import CPUDispatcher   # noqa: E402
from tools.measure.warm_year_profile import warmed_game   # noqa: E402

_kernel = {"seconds": 0.0, "calls": 0}
_by_kernel = {}


def wrap_kernels():
    """Time every call from Python into a compiled kernel, at the dispatcher class's call: no module's names change,
    so a kernel compiled for a new signature mid-run still finds the kernels it calls. The number of kernels loaded."""
    untimed = CPUDispatcher.__call__

    def kernel_call(dispatcher, *arguments, **keywords):
        started = time.perf_counter()
        try:
            return untimed(dispatcher, *arguments, **keywords)
        finally:
            seconds = time.perf_counter() - started
            _kernel["seconds"] += seconds
            _kernel["calls"] += 1
            entry = _by_kernel.setdefault(dispatcher.py_func.__module__ + "." + dispatcher.py_func.__name__, [0.0, 0])
            entry[0] += seconds
            entry[1] += 1
    CPUDispatcher.__call__ = kernel_call
    return sum(1 for module_name, module in list(sys.modules.items()) if module is not None and module_name.startswith("sim.")
               for value in vars(module).values() if isinstance(value, CPUDispatcher))


def _timed(name, function, totals):
    def phase_call(*arguments, **keywords):
        started, kernel_before, calls_before = time.perf_counter(), _kernel["seconds"], _kernel["calls"]
        try:
            return function(*arguments, **keywords)
        finally:
            entry = totals.setdefault(name, [0.0, 0.0, 0, 0])
            entry[0] += time.perf_counter() - started
            entry[1] += _kernel["seconds"] - kernel_before
            entry[2] += 1
            entry[3] += _kernel["calls"] - calls_before
    return phase_call


def wrap_year_phases(totals):
    from sim.engine import year_phases
    for index, phase in enumerate(year_phases.SHIPPED):
        year_phases.SHIPPED[index] = phase.__class__(**{**phase.__dict__, "handler": _timed(phase.name, phase.handler, totals)})


def _direct_calls(function):
    """(kind, owner, attribute) of each call in `function`'s own body: a bare name, `module.name` or `self.method`."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        if isinstance(target, ast.Name):
            calls.append(("name", None, target.id))
        elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
            calls.append(("attribute", target.value.id, target.attr))
    return list(dict.fromkeys(calls))


def wrap_economy_calls(totals):
    from sim.economy import economy as economy_module
    economy_class = economy_module.Economy
    space = vars(economy_module)
    for kind, owner, attribute in _direct_calls(economy_class._run_year):
        if kind == "name":
            value = space.get(attribute)
            if inspect.isfunction(value):
                space[attribute] = _timed("economy:" + attribute, value, totals)
        elif owner == "self":
            value = economy_class.__dict__.get(attribute)
            if inspect.isfunction(value):
                setattr(economy_class, attribute, _timed("economy:self." + attribute, value, totals))
        elif inspect.ismodule(space.get(owner)):
            module = space[owner]
            value = getattr(module, attribute, None)
            if inspect.isfunction(value) and not getattr(value, "_phase_timed", False):
                timed = _timed("economy:%s.%s" % (owner, attribute), value, totals)
                timed._phase_timed = True
                setattr(module, attribute, timed)
    economy_class.step = _timed("economy:step (whole)", economy_class.step, totals)


def main(save_path, repeat):
    game = warmed_game(save_path)
    kernels = wrap_kernels()
    totals = {}
    wrap_year_phases(totals)
    wrap_economy_calls(totals)
    walls = []
    for _ in range(repeat):
        started = time.perf_counter()
        game.step()
        walls.append(time.perf_counter() - started)
    print("kernels wrapped %d; kernel calls per year %d; years %d; wall per year %s"
          % (kernels, _kernel["calls"] // repeat, repeat, " ".join("%.3f" % wall for wall in walls)))
    print("kernel time per year %.3f s" % (_kernel["seconds"] / repeat))
    print("%-58s %8s %8s %8s %7s %8s" % ("phase or economy call (per year)", "wall", "kernel", "python", "calls", "kernels"))
    for name, (wall, kernel, calls, kernel_calls) in sorted(totals.items(), key=lambda item: -(item[1][0] - item[1][1])):
        if wall / repeat < 0.002:
            continue
        print("%-58s %8.3f %8.3f %8.3f %7d %8d" % (name, wall / repeat, kernel / repeat, (wall - kernel) / repeat, calls // repeat,
                                                kernel_calls // repeat))
    print("\n%-76s %8s %7s" % ("kernel called from Python, most called first (per year)", "seconds", "calls"))
    for name, (seconds, calls) in sorted(_by_kernel.items(), key=lambda item: -item[1][1])[:25]:
        print("%-76s %8.3f %7d" % (name, seconds / repeat, calls // repeat))


if __name__ == "__main__":
    arguments = sys.argv[1:]
    repeat = 1
    if "--repeat" in arguments:
        position = arguments.index("--repeat")
        repeat = int(arguments[position + 1])
        del arguments[position:position + 2]
    main(arguments[0], repeat)
