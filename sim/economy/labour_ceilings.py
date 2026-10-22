"""The most each trade of one run may be bid, with the run's surplus shared among its trades."""

from typing import Dict, Mapping


def joint_labour_ceilings(hours_per_run: Mapping[str, float], last_wages: Mapping[str, float],
                          surplus: float) -> Dict[str, float]:
    """Maximum wage per trade, so that the run's hours at those wages cost exactly the surplus (value of
    output less material inputs) and no more. A trade's claim on the surplus is what the market asked of its
    hours last (last wage times hours): each trade's maximum is its last wage scaled by surplus over the
    last-wage bill. That equals the last wage plus the trade's share of the surplus over the bill, shared in
    proportion to its part of the bill, so a paying run leaves every trade at least its last wage and a run
    that does not pay cuts every trade by the same share. One trade gets the whole surplus per hour. Trades
    with no wage seen share the surplus by hours."""
    total_hours = sum(hours_per_run.values())
    bill = sum(hours * last_wages.get(trade, 0.0) for trade, hours in hours_per_run.items())
    room = max(0.0, surplus)
    if bill <= 0.0:
        return {trade: room / total_hours for trade in hours_per_run}
    return {trade: last_wages.get(trade, 0.0) * room / bill for trade in hours_per_run}
