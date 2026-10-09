"""Tenure: retained worker-years each trade has spent running each technique (Complaint 111).

A plain dict {trade: {technique: worker-years}}, kept beside the labour core's people by trade so the
save round-trips it with no field list. It fades as people leave work (the demography's death and
retirement rate) and as people leave the trade; a worker who moves trade carries nothing.
"""
from typing import Dict, Mapping

Tenure = Dict[str, Dict[str, float]]


def add_tenure(tenure: Tenure, technique: str, years_by_trade: Mapping[str, float]) -> None:
    """Worker-years the trades spent running the technique."""
    for trade, years in years_by_trade.items():
        if years > 0.0:
            held = tenure.setdefault(trade, {})
            held[technique] = held.get(technique, 0.0) + years


def tenure_by_trade(tenure: Tenure, technique: str) -> Dict[str, float]:
    return {trade: held[technique] for trade, held in sorted(tenure.items()) if held.get(technique, 0.0) > 0.0}


def tenure_held(tenure: Tenure, technique: str) -> float:
    """Worker-years every trade holds in the technique."""
    return sum(tenure_by_trade(tenure, technique).values())


def outflow_shares(before: Mapping[str, float], after: Mapping[str, float], leavers_share: float) -> Dict[str, float]:
    """Share of each trade's people who left it for another trade or place, beyond those who left work:
    last year's people less the leavers, against this year's. Growth is no outflow."""
    shares = {}
    for trade, now in after.items():
        kept = before.get(trade, 0.0) * (1.0 - leavers_share)
        shares[trade] = max(0.0, 1.0 - now / kept) if kept > 0.0 else 0.0
    return shares


def fade_tenure(tenure: Tenure, leavers_share: float, outflow: Mapping[str, float] = None) -> None:
    """Keep the share of each trade's tenure that stays: those who neither left work nor left the trade."""
    for trade, held in tenure.items():
        kept = (1.0 - min(1.0, leavers_share)) * (1.0 - min(1.0, (outflow or {}).get(trade, 0.0)))
        for technique in held:
            held[technique] *= kept
