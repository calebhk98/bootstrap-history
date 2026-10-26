"""The state reporting owns for each seat."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class ReportingSeat:
    log: List[Tuple[Any, str]] = field(default_factory=list)               # (year, LogLine) in the order they happened
    automation_audit: List[Dict[str, Any]] = field(default_factory=list)   # the last few years' rows (rules.py)
