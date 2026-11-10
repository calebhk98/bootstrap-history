"""Every compiled table type (a namedtuple class under sim/) is reachable by its own name in its own module.

numba's on-disk cache stores a kernel's argument types by module and class name; a table class whose name differs from the
module attribute that holds it (`Requests = TableSpec("ClearingRequests", ...).make_type(__name__)`) is written to the cache
but never found on load, so its kernels compile again in every process.

    python3 tools/check_table_names.py      # prints each mismatch; exit 1 if any
"""
import importlib
import os
import pkgutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sim  # noqa: E402


def mismatches():
    """`module.attribute is class Name` for each namedtuple class held under a name it cannot be found by."""
    found = []
    for module_info in pkgutil.walk_packages(sim.__path__, "sim."):
        if ".tests" in module_info.name:
            continue
        try:
            module = importlib.import_module(module_info.name)
        except Exception:      # a module that needs optional parts is not this check's concern
            continue
        for attribute, value in vars(module).items():
            if (isinstance(value, type) and issubclass(value, tuple) and hasattr(value, "_fields")
                    and value.__module__ == module_info.name and getattr(module, value.__name__, None) is not value):
                found.append("%s.%s is class %s" % (module_info.name, attribute, value.__name__))
    return sorted(set(found))


if __name__ == "__main__":
    problems = mismatches()
    for problem in problems:
        print(problem)
    sys.exit(1 if problems else 0)
