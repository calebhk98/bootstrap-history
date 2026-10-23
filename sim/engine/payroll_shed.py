"""The staff a household cannot pay leave: whole people, dearest trade first, and the loss is always written in the log."""

from sim.refusal import LogLine

from .payroll_trim import staff_to_let_go

MIN_STAFF_GONE_TO_LOG = 0.005


def shed_unpayable_staff(game, payroll, can_pay):
    """Let go the part of `payroll` that `can_pay` does not cover from the household in `game` (the game: its
    `state`, `labour`). Logs `staff_left_unpaid` with the people gone when any went; returns the people gone."""
    household = game.state.household
    labour = game.labour
    if payroll <= can_pay or not household.employees:
        return 0.0
    gone = 0.0
    staff_before = labour.staff_snapshot()
    for trade_id, cut in staff_to_let_go(payroll, can_pay, dict(household.employees), labour.market.quote_annual).items():
        labour.add_employed(trade_id, -cut)
        gone += cut
        if labour.employed(trade_id) < 0.5:
            labour.set_employed(trade_id, 0.0)
    labour.resync_pools()
    labour.log_staff_reduction("a payroll you cannot meet", staff_before)
    if gone > MIN_STAFF_GONE_TO_LOG:
        household.log.append((game.state.scenario.year, LogLine(
            "staff_left_unpaid", "you cannot pay everyone: %.1f of your staff leave for work that pays" % gone, staff_gone=gone)))
    return gone
