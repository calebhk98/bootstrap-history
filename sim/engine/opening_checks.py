"""Relationship checks on a civilisation's full-length opening (Complaint 523).

Pure functions over figures read from an opened game (opening_checks_run.py gathers them); each returns a
`CheckResult`: the measured value, the bound it is held to and whether it passes. They are relationships, never
dated values (CLAUDE.md 4.2): a price over its making cost, a money stock against the wear that drains it, a
wage over the floor a household needs, whether the spin-up stopped moving.
"""
import math
from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Sequence

from sim.economy.metal_stock import COIN_WEAR_PER_YEAR

# A price within an order of magnitude of what making the good costs: above it a worker-hour in making it sells
# for many wages, below it nobody would make it. An order of magnitude is the widest grade spread among one
# metal's deposits, the most that scarcity rent on a sited ore can be (Complaints/519).
PRICE_OVER_COST_BOUND = 10.0
# The unskilled wage covers the household's floor; below it workers cannot keep a household fed.
WAGE_OVER_FLOOR_LOWEST = 1.0
# A decade of the money trace; the stock may lag a decade of unreplaced wear and no more (Complaints/473).
DECADE_YEARS = 10


@dataclass(frozen=True)
class CheckResult:
    """One check: `value` measured, `bound` it is held to (`bound_kind` says whether the value must stay "within"
    a ratio band of the bound, or be "at least" or "at most" the bound), `passed`, and `detail` (plain data the
    table can show)."""
    name: str
    value: Optional[float]
    bound: float
    bound_kind: str
    passed: bool
    detail: Mapping[str, object]

    def to_plain(self) -> Dict[str, object]:
        return {"name": self.name, "value": self.value, "bound": self.bound, "bound_kind": self.bound_kind,
                "passed": self.passed, "detail": dict(self.detail)}


def price_over_cost(name: str, ratios: Mapping[str, float], bound: float = PRICE_OVER_COST_BOUND) -> CheckResult:
    """`ratios` is {good: price over its making cost}. The value is the ratio furthest from one (in either
    direction); the check passes when every ratio stands between 1/bound and bound. No ratio: no value, and fail
    (a check that measured nothing has not passed)."""
    usable = {good: ratio for good, ratio in ratios.items() if ratio > 0.0 and math.isfinite(ratio)}
    if not usable:
        return CheckResult(name, None, bound, "within", False, {"ratios": {}, "outside": {}})
    worst = max(usable.values(), key=lambda ratio: abs(math.log(ratio)))
    outside = {good: ratio for good, ratio in usable.items() if ratio > bound or ratio < 1.0 / bound}
    return CheckResult(name, worst, bound, "within", not outside, {"ratios": dict(usable), "outside": outside})


def money_against_wear(rows: Sequence[Mapping[str, float]], wear_share: float = COIN_WEAR_PER_YEAR,
                       decade: int = DECADE_YEARS) -> CheckResult:
    """`rows` are the spin-up trace's years (economy_port_trace.spin_up_trace). The value is the money stock of the
    last decade over that of the first decade. Unreplaced wear leaves (1 - wear) to the decade's power after one
    decade, and that is the lowest a mint that is replacing the wear may leave it (a lag of one decade is
    allowed, no more). Fewer than two decades of trace: no value, and fail."""
    bound = (1.0 - wear_share) ** decade
    if len(rows) < 2 * decade:
        return CheckResult("money_against_wear", None, bound, "at least", False, {"years": len(rows)})
    first = math.fsum(row["money_supply"] for row in rows[:decade]) / decade
    last = math.fsum(row["money_supply"] for row in rows[-decade:]) / decade
    worn = math.fsum(row["wear"] for row in rows[-decade:])
    replaced = math.fsum(row["struck"] for row in rows[-decade:]) / worn if worn > 0.0 else math.nan
    value = last / first if first > 0.0 else None
    return CheckResult("money_against_wear", value, bound, "at least", value is not None and value >= bound,
                       {"years": len(rows), "last_decade_struck_over_wear": replaced})


def wage_over_floor(wage: Optional[float], floor: Optional[float],
                    lowest: float = WAGE_OVER_FLOOR_LOWEST) -> CheckResult:
    """The unskilled wage per hour over the wage floor per hour (what the worker's household costs less its
    plot). No wage or no floor (a plot that feeds the household leaves nothing to compare): no value, and fail."""
    if not wage or not floor or floor <= 0.0:
        return CheckResult("wage_over_floor", None, lowest, "at least", False, {"wage": wage, "floor": floor})
    value = wage / floor
    return CheckResult("wage_over_floor", value, lowest, "at least", value >= lowest, {"wage": wage, "floor": floor})


def spin_up_settled(result: Mapping[str, object], tolerance: float) -> CheckResult:
    """`result` is the opening's `spin_up_result` ({settled, years, gap}). The value is the largest yearly change
    in the last year measured and the bound the tolerance the stage was held to."""
    if not result:
        return CheckResult("spin_up_settled", None, tolerance, "at most", False, {"years": None})
    return CheckResult("spin_up_settled", float(result["gap"]), tolerance, "at most", bool(result["settled"]),
                       {"years": result["years"]})
