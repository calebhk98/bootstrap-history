"""Profile the second (warm) year of a saved game with every compiled kernel as its own profile entry.

cProfile does not see a call into a numba dispatcher, so a kernel's time lands in its Python caller's own time. Here each
dispatcher held by a `sim.` module is replaced by a plain Python function named `kernel__<module>__<function>` that calls
it, so what is left as a function's own time is Python. Run from the repository root:

    python3 tools/measure/warm_year_split_profile.py SAVE.json OUT.prof
    python3 -c "import pstats; pstats.Stats('OUT.prof').sort_stats('tottime').print_stats(40)"

The save is read, never written. Kernels a kernel calls are inside their caller's entry. cProfile inflates Python time
(about two to three times); compare profiles with each other, and process time with `warm_year_cpu.py`."""
import cProfile
import sys

sys.path.insert(0, ".")
from numba.core.registry import CPUDispatcher   # noqa: E402
from tools.measure.warm_year_profile import warmed_game   # noqa: E402


def named_caller(name, dispatcher):
    """A Python function named after the kernel that calls `dispatcher`, so the profile lists it."""
    function_name = "kernel__" + name.replace(".", "__")
    space = {"dispatcher": dispatcher}
    exec("def %s(*args, **kwargs):\n    return dispatcher(*args, **kwargs)\n" % function_name, space)
    return space[function_name]


def wrap_kernels():
    """Replace every dispatcher held by a loaded `sim.` module with its named caller; the number wrapped."""
    callers = {}
    for module_name, module in list(sys.modules.items()):
        if module is None or not module_name.startswith("sim."):
            continue
        for attribute, value in list(vars(module).items()):
            if isinstance(value, CPUDispatcher):
                if id(value) not in callers:
                    callers[id(value)] = named_caller("%s.%s" % (value.py_func.__module__, value.py_func.__name__), value)
                setattr(module, attribute, callers[id(value)])
    return len(callers)


def main(save_path, out_path):
    game = warmed_game(save_path)
    wrap_kernels()
    profiler = cProfile.Profile()
    profiler.enable()
    game.step()
    profiler.disable()
    profiler.dump_stats(out_path)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
