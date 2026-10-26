"""The shape of a log line and an audit row, and which rows are kept and read: plain values in, plain values out.

Each row of the audit trail is {"year", "policy", "action", "what", "reason", "cost"}, plus "ids" when it names
concerns and, where the reason has a stable code, "reason_kind" with the figures it states beside it. `cost` is the
change in capital across the action, measured where the action ran, so it is the same money the books moved."""
from typing import Any, Dict, List, Tuple

from sim.refusal import LogLine

YEARS_KEPT = 5


def log_entry(year: int, kind: str, text: str, facts: Dict[str, Any]) -> Tuple[int, str]:
    return year, LogLine(kind, text, **facts)


def audit_row(year: int, policy: str, action: str, what: str, reason: str, capital_before: float, capital_now: float,
              extra: Dict[str, Any]) -> Dict[str, Any]:
    return {"year": year, "policy": policy, "action": action, "what": what, "reason": reason,
            "cost": round(capital_before - capital_now, 1), **extra}


def kept_rows(rows: List[Dict[str, Any]], year: int) -> List[Dict[str, Any]]:
    """The rows newer than the years kept."""
    return [row for row in rows if row["year"] > year - YEARS_KEPT]


def recent_rows(rows: List[Dict[str, Any]], year: int, years: Any = 1) -> List[Dict[str, Any]]:
    """The rows from the latest `years` years that were played, oldest first."""
    first_year = year - max(1, int(years))
    return [row for row in rows if row["year"] >= first_year]


def order_id(policy: str, subject: str, year: int) -> str:
    """The id an order carries from its audit row to what it set going (a mine tranche, then the working)."""
    return "%s:%s:%d" % (policy, subject, year)
