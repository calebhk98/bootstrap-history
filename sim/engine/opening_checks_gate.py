"""The `openings` command's gate: an opening that fails the checks (opening_checks.py) is not shipped."""
from typing import List, Optional, Tuple

from . import opening_checks_run, opening_checks_table, shipped_openings


class OpeningGate:
    """Called with the opened game before its entries are written (shipped_openings_build.build_reporting).
    Raises SystemExit naming the failed checks unless `allow_failing` gives a reason, which is printed. A passing
    (or allowed) opening also ships its money trace, so the next check of it is a cache read."""

    def __init__(self, civ_id: str, allow_failing: Optional[str] = None):
        self.civ_id = civ_id
        self.allow_failing = allow_failing
        self.results = []
        self.shipped: List[Tuple[str, str]] = []

    def __call__(self, game) -> None:
        self.results = opening_checks_run.check_game(game)
        print("\n".join(opening_checks_table.table({self.civ_id: self.results})), flush=True)
        failed = opening_checks_run.failures(self.results)
        if failed and not self.allow_failing:
            raise SystemExit("%s: not shipped; failing checks: %s (pass --allow-failing REASON to ship it anyway)"
                             % (self.civ_id, ", ".join(each.name for each in failed)))
        if failed:
            print("%s: shipping an opening that fails %s; reason: %s"
                  % (self.civ_id, ", ".join(each.name for each in failed), self.allow_failing), flush=True)
        namespace, key = opening_checks_run.trace_entry(game)
        shipped_openings.write(namespace, key, opening_checks_run.opening_trace(game))
        self.shipped.append((namespace, key))
