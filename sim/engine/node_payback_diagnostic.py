"""Diagnostic: nodes whose build cost is repaid suspiciously fast by their net earnings.

A new technique may earn a fortune until its own output drives the price down, so
nothing here caps or blocks anything; a fast payback only flags a possible fault
(a mispriced input, a missing cost, an output the plant could not make)."""
from typing import Any, Dict, List, Mapping

from sim.constants import declare

SUSPICIOUS_PAYBACK_YEARS = declare(
    "SUSPICIOUS_PAYBACK_YEARS", 0.25, kind="temporary_heuristic", unit="years", source=None,
    confidence="D",
    why="A node that repays its whole build cost from net earnings faster than this is "
        "listed for a human to look at. It never changes revenue.")


def fast_payback_rows(nodes: Mapping[str, dict],
                      threshold_years: float = SUSPICIOUS_PAYBACK_YEARS) -> List[Dict[str, Any]]:
    """Rows for nodes whose build cost over net yearly earnings (revenue less upkeep, which
    holds staff wages and plant wear) is under `threshold_years`, quickest first."""
    rows = []
    for node_id, node in nodes.items():
        net = float(node.get("rev") or 0.0) - float(node.get("up") or 0.0)
        cost = float(node.get("_total_cost") or 0.0)
        if net <= 0.0 or cost <= 0.0 or cost / net >= threshold_years:
            continue
        rows.append({"node": node_id, "basis": node.get("_revenue_basis"), "build_cost": cost,
                     "net_per_year": net, "payback_years": cost / net})
    return sorted(rows, key=lambda row: row["payback_years"])


def format_rows(rows: List[Dict[str, Any]]) -> List[str]:
    if not rows:
        return ["  no node repays its build cost from net earnings faster than the diagnostic threshold"]
    return ["  %-32s %-10s payback %.3f years (build %.4g, net %.4g a year)"
            % (row["node"], row["basis"], row["payback_years"], row["build_cost"], row["net_per_year"])
            for row in rows]
