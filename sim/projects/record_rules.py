"""The record of a project in hand and of one stopped, as plain functions of the figures they hold."""
from typing import Any, Dict, Mapping, Optional, Tuple


def new_record(node: Mapping[str, Any], rebuild_factor: float, ph_left: Optional[float], spent: float,
               cost_left: float, include_labour: bool, bill: Optional[float], own_output_claim: Optional[Mapping[str, float]]) -> Dict[str, Any]:
    """One consistently-shaped active project. Hours and labour left start full (scaled by the share of the work a
    rebuild leaves), so the hired-labour total is not guessed later from founder hours already spent."""
    record = dict(
        ph_left=float(node["ph"] * rebuild_factor if ph_left is None else ph_left),
        yrs=0.0, spent=float(spent),
        cost_left=float(cost_left),
        status="ACTIVE")
    if rebuild_factor < 1.0:
        record["rebuild_factor"] = rebuild_factor
    if bill is not None:
        record["bill"] = float(bill)
    if own_output_claim:
        record["own_output_claim"] = own_output_claim
    if include_labour:
        record["lab_left"] = {trade: hours * rebuild_factor for trade, hours in node["lab"].items()}
    return record


def credit_kept(spent: float, credit_before: float) -> Tuple[float, Optional[float]]:
    """(the money a stopped project keeps, the credit it then stands for or None when nothing worth keeping was paid).
    Money already spent stands against the node and comes off the bill if it is begun again; the hours are gone."""
    kept = max(0.0, spent)
    return kept, (credit_before + kept if kept > 0.5 else None)
