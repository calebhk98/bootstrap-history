"""The opening checks as a table of plain lines (the `opening-checks` command and the `openings` gate)."""
from typing import Dict, Iterable, List

from .opening_checks import CheckResult

BOUND_FORMATS = {"at least": ">= %.4g", "at most": "<= %.4g"}


def bound_text(result: CheckResult) -> str:
    if result.bound_kind == "within":
        return "%.4g..%.4g" % (1.0 / result.bound, result.bound)
    return BOUND_FORMATS[result.bound_kind] % result.bound


def value_text(result: CheckResult) -> str:
    return "n/a" if result.value is None else "%.4g" % result.value


def row(civ_id: str, result: CheckResult) -> str:
    return "%-16s %-26s %10s  %-14s %s" % (civ_id, result.name, value_text(result), bound_text(result),
                                          "pass" if result.passed else "FAIL")


def header() -> str:
    return "%-16s %-26s %10s  %-14s %s" % ("civilisation", "check", "value", "bound", "result")


def table(results_by_civ: Dict[str, Iterable[CheckResult]], with_header: bool = True) -> List[str]:
    """A header, then one line per civilisation and check; a failing price check names the goods outside the band."""
    lines = [header()] if with_header else []
    for civ_id, results in results_by_civ.items():
        for result in results:
            lines.append(row(civ_id, result))
            for good, ratio in sorted(dict(result.detail.get("outside") or {}).items()):
                lines.append("%-16s   outside the band: %s at %.4g" % ("", good, ratio))
    return lines
