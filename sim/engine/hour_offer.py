"""How the founder's yearly hours are shared among active projects: the queue they draw in, what one project is
offered, and why a standing directive may go unmet. Plain arithmetic on the numbers handed in."""

SHORTFALL_TOLERANCE = 1.0
PACE_TOLERANCE = 0.5
THROTTLE_NOTICED_BELOW = 0.98


def priority_queue(active_ids, order, allocations):
    """Active project ids in the order they draw on the hour pool: those with a standing allocation first, then the
    rest by their place in `order` (ids absent from it last)."""
    position = {}
    for index, node_id in enumerate(order):
        position.setdefault(node_id, index)
    return sorted(active_ids, key=lambda node_id: (
        0 if allocations.get(node_id, 0.0) > 0 else 1,
        position.get(node_id, 9999)))


def hours_offered(remaining, pace_cap, directed_hours, throttle):
    """The hours one project is offered: what is left of the pool, its own pace and any standing directive (a
    ceiling, never a floor), whichever is least, scaled by the shortage throttle."""
    if directed_hours and directed_hours > 0:
        return min(remaining, pace_cap, directed_hours) * throttle
    return min(remaining, pace_cap) * throttle


def unmet_directive_cause(directed_hours, offered, pace_cap, throttle, shortage_binding):
    """Why a standing directive was not met in full ('shortage_throttle', 'own_pace' or 'pool_claimed'), or None
    when it was met (to within an hour) or there is none."""
    if not (directed_hours and directed_hours > 0 and directed_hours - offered > SHORTFALL_TOLERANCE):
        return None
    if throttle < THROTTLE_NOTICED_BELOW and shortage_binding and pace_cap >= directed_hours - PACE_TOLERANCE:
        return "shortage_throttle"
    if pace_cap * throttle < directed_hours - PACE_TOLERANCE:
        return "own_pace"
    return "pool_claimed"
