"""When a trade a project needs will first have hands: the start gate, the start reply and the stall gate read one rule."""

# A project with no hands in a trade it owes hours to is abandoned on this stalled year.
STALL_YEARS_BEFORE_ABANDONMENT = 4


def years_until_trade_has_hands(sim, trade):
    """0 when hands exist now; else years until the soonest trainees join; None when nobody is on the way."""
    if sim.labour.market_supply(trade) > 0.0:
        return 0.0
    year = sim.state.scenario.year
    waits = [max(0.0, row[1] - year) for row in sim.state.household.training
             if len(row) > 3 and row[2] == trade and row[3] > 0]
    return min(waits) if waits else None


def trades_the_project_waits_for(sim, node_id):
    """{trade: years until the first hands} for each trade the project owes hours to that nobody holds yet."""
    waits = {}
    for trade, want in (sim.nodes[node_id].get("lab") or {}).items():
        wait = years_until_trade_has_hands(sim, trade) if want > 0 else 0.0
        if wait is None or wait > 0.0:
            waits[trade] = wait
    return waits


def trade_wait_outlasts_the_project(sim, trade):
    """True when no hands exist and none arrive before the stall gate would abandon the project."""
    wait = years_until_trade_has_hands(sim, trade)
    return wait is None or wait >= STALL_YEARS_BEFORE_ABANDONMENT - 1
