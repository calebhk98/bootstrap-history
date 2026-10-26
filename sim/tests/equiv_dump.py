"""Run the equivalence tool's dump against another checkout:

    cd BASE && python3 CURRENT/sim/tests/equiv_dump.py BASE CURRENT/sim/tests SCENARIO_JSON YEAR OUT raw SPIN_UP

BASE's `sim` package is imported; the tool's own modules are loaded from CURRENT's files (BASE need not have them)."""
import importlib.util, os, sys


def load_tool_module(name, tool_directory):
    spec = importlib.util.spec_from_file_location("sim.tests." + name, os.path.join(tool_directory, name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules["sim.tests." + name] = module
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    base_directory, tool_directory = os.path.abspath(sys.argv[1]), sys.argv[2]
    sys.path[0:1] = [base_directory]
    os.chdir(base_directory)
    import sim.tests
    for module_name in ("equiv_core", "equiv_fields", "equiv_run"):
        setattr(sim.tests, module_name, load_tool_module(module_name, tool_directory))
    sys.exit(sys.modules["sim.tests.equiv_run"].main_dump(sys.argv[3:]))
