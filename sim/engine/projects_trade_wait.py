"""When a trade a project needs will first have hands: the start gate, the start reply and the stall gate read one rule
(sim/projects/start_rules.py `trade_wait_years`, `trade_wait_outlasts`)."""
from sim.projects.api import start_rules

STALL_YEARS_BEFORE_ABANDONMENT = start_rules.STALL_YEARS_BEFORE_ABANDONMENT


def years_until_trade_has_hands(sim, trade):
    """0 when hands exist now; else years until the soonest trainees join; None when nobody is on the way."""
    return start_rules.trade_wait_years(sim.labour.market_supply(trade), sim.state.scenario.year, sim.state.household.training, trade)


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
    return start_rules.trade_wait_outlasts(years_until_trade_has_hands(sim, trade), STALL_YEARS_BEFORE_ABANDONMENT)
