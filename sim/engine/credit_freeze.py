"""The rules of a run stuck in arrears: when lenders stop lending after a settlement, and when the run has stalled."""

STALL_MINIMUM_INSOLVENT_YEARS = 8


def settlement_freeze(frozen_before, year, freeze_years):
    """(the year nobody lends until, whether this settlement moved a freeze still in force). A freeze already
    running is never shortened; settling while it runs pushes its date out."""
    frozen_until = max(frozen_before, year + freeze_years)
    moved = frozen_before > year and frozen_until > frozen_before
    return frozen_until, moved


def settlement_owed(limit, marked_down_limit, retained_fraction):
    """What is still owed after a write-off: a share of the line that stands once the name has been marked down
    (never of a line above the one the debtor had), so the balance never starts outside the line."""
    return min(limit, marked_down_limit) * retained_fraction


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


def halt_active_projects(projects):
    """Stop every project in hand: (their names in order, what had been paid towards them). What was paid is
    credited to the project in `paid_towards`, not burned, and a bounty on it lapses."""
    halted = sorted(projects.active)
    paid_towards = getattr(projects, "paid_towards", None)
    if paid_towards is None:
        paid_towards = projects.paid_towards = {}
    kept = 0.0
    for node_id in halted:
        entry = projects.active.pop(node_id, None)
        if entry:
            spent = entry.get("spent", 0.0) if isinstance(entry, dict) else getattr(entry, "spent", 0.0)
            paid_towards[node_id] = paid_towards.get(node_id, 0.0) + max(0.0, spent)
            kept += max(0.0, spent)
        projects.bountied.discard(node_id)
    return halted, kept
