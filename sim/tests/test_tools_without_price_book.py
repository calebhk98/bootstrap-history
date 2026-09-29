"""Tools must not depend on data/prices.json for namespaces or validation.

Each tool runs in a subprocess where opening prices.json raises, so a tool
that still reaches the file (directly or through the main loader) fails here.
Wages and solved prices come from the wage provider and the solver, so cost
figures are still produced with the book unreadable.
"""
from .harness import *  # noqa: F401,F403

_BLOCKED_RUNNER = """
import builtins, runpy, sys
real_open = builtins.open
def guarded_open(path, *args, **kwargs):
    if str(path).endswith("prices.json"):
        raise FileNotFoundError(path)
    return real_open(path, *args, **kwargs)
builtins.open = guarded_open
script = sys.argv[1]
sys.argv = sys.argv[1:]
runpy.run_path(script, run_name="__main__")
"""


def _run_without_book(script, *arguments):
    return subprocess.run(
        [sys.executable, "-c", _BLOCKED_RUNNER, os.path.join(ROOT, "sim", script)] + list(arguments),
        capture_output=True, text=True, timeout=600, cwd=ROOT)


_validation = _run_without_book("validate_production.py")
check("validate_production runs with the price book unreadable",
      _validation.returncode == 0 and "problem(s)" in _validation.stdout,
      (_validation.stdout + _validation.stderr)[-400:])

_judge = _run_without_book("treetool.py", "judge")
check("treetool judge runs with the price book unreadable",
      _judge.returncode == 0 and "PER-TECHNOLOGY AUDIT" in _judge.stdout,
      (_judge.stdout + _judge.stderr)[-400:])

_audit = _run_without_book("audit_costs.py")
check("audit_costs prices the cost base with the price book unreadable",
      _audit.returncode == 0 and "unavailable" not in _audit.stdout,
      (_audit.stdout + _audit.stderr)[-400:])

_report = _run_without_book("solve_prices.py", "--why", "iron_bar_kg")
check("solve_prices explains a price from the wage provider without the price book",
      _report.returncode == 0 and "labour-hours" in _report.stdout and "Traceback" not in _report.stderr,
      (_report.stdout + _report.stderr)[-400:])

_merge = _run_without_book("treetool.py", "merge")
check("treetool merge takes its material namespace from the catalogue with the price book unreadable",
      "Traceback" not in _merge.stderr and ("UNDECLARED" in _merge.stdout or _merge.returncode == 0),
      (_merge.stdout + _merge.stderr)[-400:])

_compare = subprocess.run([sys.executable, os.path.join(ROOT, "sim", "solve_prices.py"), "--compare"],
                          capture_output=True, text=True, timeout=120, cwd=ROOT)
check("solve_prices no longer offers a comparison against book values",
      _compare.returncode != 0 and "unrecognized arguments" in _compare.stderr,
      _compare.stderr[-300:])
