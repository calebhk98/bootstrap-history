"""Stopping every project in hand at once: what a household past its credit limit can no longer fund."""


def halt_active_projects(active, paid_towards, bountied):
    """Stop every project in hand: (their names in order, what had been paid towards them). What was paid is
    credited to the project in `paid_towards`, not burned, and a bounty on it lapses."""
    halted = sorted(active)
    kept = 0.0
    for node_id in halted:
        entry = active.pop(node_id, None)
        if entry:
            spent = entry.get("spent", 0.0) if isinstance(entry, dict) else getattr(entry, "spent", 0.0)
            paid_towards[node_id] = paid_towards.get(node_id, 0.0) + max(0.0, spent)
            kept += max(0.0, spent)
        bountied.discard(node_id)
    return halted, kept
