"""Which trades a project wants more hours of than the society can ever field (`start` says so at the time)."""


def trades_beyond_ceiling(wants_by_trade, years, ceiling_of):
    """[(trade, hours a year wanted, hours a year the society can call on)] for each trade whose yearly share of the
    project's hours is more than `ceiling_of(trade)`; the share is the total over the project's calendar years."""
    share = min(1.0, 1.0 / max(1.0, years))
    beyond = []
    for trade, want in (wants_by_trade or {}).items():
        need = want * share
        ceiling = ceiling_of(trade)
        if need > 0 and ceiling < need:
            beyond.append((trade, need, max(0.0, ceiling)))
    return beyond
