"""The most each trade of one run may be bid, with the run's surplus shared among its trades."""

from typing import Dict, Mapping


def joint_labour_ceilings(hours_per_run: Mapping[str, float], last_wages: Mapping[str, float],
                          surplus: float) -> Dict[str, float]:
    """Maximum wage per trade, so that the run's hours at those wages cost exactly the surplus (value of
    output less material inputs) and no more. A trade's claim on the surplus is what the market asked of its
    hours last (last wage times hours): each trade's maximum is its last wage scaled by surplus over the
    last-wage bill. That equals the last wage plus the trade's share of the surplus over the bill, shared in
    proportion to its part of the bill, so a paying run leaves every trade at least its last wage and a run
    that does not pay cuts every trade by the same share. One trade gets the whole surplus per hour. A trade
    with no wage seen claims like the priced trades' average hour (their bill over their hours), so it shares
    the surplus by its hours at that wage and is never left at nothing; with no wage seen for any trade the
    trades share the surplus by hours. A run with no hours has no ceilings."""
    total_hours = sum(hours_per_run.values())
    if total_hours <= 0.0:      # a run that hires no hours has no trade to bid
        return {}
    priced = {trade: hours for trade, hours in hours_per_run.items() if trade in last_wages}
    priced_bill = sum(hours * last_wages[trade] for trade, hours in priced.items())
    room = max(0.0, surplus)
    if priced_bill <= 0.0:
        return {trade: room / total_hours for trade in hours_per_run}
    priced_trades_average_wage = priced_bill / sum(priced.values())     # a claim on the surplus, not a wage rule (trade_wages)
    claimed = {trade: last_wages.get(trade, priced_trades_average_wage) for trade in hours_per_run}
    bill = sum(hours * claimed[trade] for trade, hours in hours_per_run.items())
    return {trade: claimed[trade] * room / bill for trade in hours_per_run}
