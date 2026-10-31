"""Runs a producer could still add, which entry counts as supply the market already has."""


def idle_runs(capacity_runs: float, last_runs: float, pending_runs: float, land_run_cap: float) -> float:
    """Runs of capacity not worked last year, plus capacity waiting on a plant loan, never above what the land granted
    allows (`land_run_cap`, below zero for no limit): a maker held to its ground cannot meet a gap its plant is big enough
    for, so the gap still draws a newcomer on land that is free."""
    room = capacity_runs - max(0.0, last_runs) + pending_runs
    if land_run_cap >= 0.0:
        room = min(room, land_run_cap - max(0.0, last_runs))
    return max(0.0, room)
