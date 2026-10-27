"""The multipliers on a node's bare risk: what a project's chance of failing the next attempt is made of."""
from typing import Iterable


def control_relief_multiplier(failure_kind, relief_kinds_in_force: Iterable, relief_factor: float) -> float:
    """The share of risk left by a completed controller: `relief_factor` when any relief in force is for this
    `failure_kind`, else untouched."""
    return relief_factor if any(kind == failure_kind for kind in relief_kinds_in_force) else 1.0


def effective_risk_of(bare_risk: float, depth_multiplier: float, control_multiplier: float, precaution_multiplier: float) -> float:
    """The chance of failing the next attempt: the bare risk times each multiplier, which compound rather than override."""
    return bare_risk * depth_multiplier * control_multiplier * precaution_multiplier


def attempt_fails(draw: float, risk: float) -> bool:
    """One draw in [0, 1) against the chance of failing: the attempt fails when the draw falls under the risk."""
    return draw < risk
