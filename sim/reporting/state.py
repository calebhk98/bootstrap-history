"""The state reporting owns for each seat."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class ReportingWorld:
    output_per_head: float = 1.0          # real output per person over the opening's, as the market last closed
    introduction_prices: Dict[str, float] = field(default_factory=dict)   # good -> labour-hour price when first offered
    money_real: float = 1.0               # purchasing power of one coin, one at the start date
    wage_market_ratios: Dict[str, float] = field(default_factory=dict)    # material -> price ratio at the last close
    agent_baseline_prices: Dict[str, float] = field(default_factory=dict)  # good -> price at the first close read


@dataclass
class ReportingSeat:
    log: List[Tuple[Any, str]] = field(default_factory=list)               # (year, LogLine) in the order they happened
    automation_audit: List[Dict[str, Any]] = field(default_factory=list)   # the last few years' rows (rules.py)
