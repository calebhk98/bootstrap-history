"""How far a taxpayer stands past the state's notice line, what the state levies at that distance, and the tail risk of
confiscation: plain functions of numbers, called by `society_state_pressure` (Complaint 640)."""
from typing import List, Tuple


def share_past(notice: float, threshold: float) -> float:
    """0..1: how far `notice` stands past `threshold`, as a share of the remaining distance to full notice."""
    if notice <= threshold:
        return 0.0
    return min(1.0, (notice - threshold) / (1.0 - threshold))


def levy_shares_at(over: float, ordinary_rate: float, requisition_rate: float, office_rate: float,
                   protection: float, protection_discount: float) -> Tuple[float, float]:
    """(requisition, office) share of income assessed at `over` past the notice line: the ordinary rate plus the rates the
    shortfall set, nothing below the line; protection bargains requisition down, never the office."""
    if over <= 0.0:
        return 0.0, 0.0
    requisition = (ordinary_rate + requisition_rate) * over
    if protection > 0:
        requisition *= (1.0 - protection_discount * protection)
    return max(0.0, requisition), max(0.0, office_rate * over)


def confiscation_chance(over: float, max_rate: float, protection: float, protection_discount: float,
                        dispersal: float, military_leverage: float, military_discount: float) -> Tuple[float, List[int]]:
    """(yearly probability, indices of the mitigations in force) of confiscation at `over` past its line. The indices are
    0 protection, 1 dispersal of holdings, 2 usefulness to the state, in the order of the caller's labels."""
    if over <= 0.0:
        return 0.0, []
    mitigation = 1.0
    active: List[int] = []
    if protection > 0:
        mitigation *= (1.0 - protection_discount * protection)
        active.append(0)
    if dispersal > 0:
        mitigation *= (1.0 - dispersal)
        active.append(1)
    if military_leverage > 0:
        mitigation *= (1.0 - military_discount * military_leverage)
        active.append(2)
    return max_rate * over * mitigation, active


def military_demand_eligible(leverage: float, leverage_floor: float, notice: float, notice_line: float) -> bool:
    """Whether a household is militarily useful (`leverage` at its floor) and visible (`notice` past its own line)
    enough that a state which can fight would ask it for supply."""
    return leverage >= leverage_floor and notice > notice_line
