"""The rules of a run stuck in arrears: when lenders stop lending after a settlement, and when the run has stalled."""

STALL_MINIMUM_INSOLVENT_YEARS = 8


def settlement_freeze(frozen_before, year, freeze_years):
    """(the year nobody lends until, whether this settlement moved a freeze still in force). A freeze already
    running is never shortened; settling while it runs pushes its date out."""
    frozen_until = max(frozen_before, year + freeze_years)
    moved = frozen_before > year and frozen_until > frozen_before
    return frozen_until, moved


def standing_net(revenue, upkeep, living_cost, mine_cost, interest):
    """The yearly balance of a household on its standing figures: what comes in less every recurring cost."""
    return revenue - upkeep - living_cost - mine_cost - interest


def is_stalled(capital, insolvent_years, net):
    """A run has stalled when it is in arrears, has been for long enough, and still loses money every year."""
    if capital >= 0 or insolvent_years < STALL_MINIMUM_INSOLVENT_YEARS:
        return False
    return net < 0


def loss_makers(running_nodes, takings, upkeep):
    """The running concerns whose upkeep exceeds their takings, worst first (ties by name)."""
    return sorted((node_id for node_id in running_nodes if upkeep[node_id] > takings[node_id]),
                  key=lambda node_id: (takings[node_id] - upkeep[node_id], node_id))
