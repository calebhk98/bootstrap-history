"""How empty the carriers' return trips are, from the goods the merchants carried last year.

Standalone: `sim.geography.flow_ledger` and `sim.constants`.
"""
from sim.constants import declare
from sim.geography.api import flow_ledger

FLOW_IMBALANCE_STEP = declare(
    "FLOW_IMBALANCE_STEP", 0.1, kind="temporary_heuristic",
    unit="share of return trips empty", source=None, confidence="D",
    why="The carriage table and the market areas over it are rebuilt when the emptiness of the returns "
        "changes; stepping it keeps a small drift in the flows from repartitioning the markets every year.")


def flow_imbalance(record) -> float:
    """The share of carriers' return trips that find no opposite flow, last year's, in steps; 1 with no
    ledger (carriers return empty)."""
    raw = flow_ledger.overall_imbalance(record.carried)
    return min(1.0, round(raw / FLOW_IMBALANCE_STEP) * FLOW_IMBALANCE_STEP)
