"""Plain rules for what the founder's military work is worth to a patron and to a war's cost, called with figures."""
import math


def leverage_of(military_node_count, saturates_at):
    """0..1: none for no founder-built military nodes, square-root scaled, full at `saturates_at` of them."""
    if military_node_count <= 0:
        return 0.0
    return min(1.0, math.sqrt(military_node_count / saturates_at))


def war_relief(leverage, relief_cap):
    """(multiplier on a war's output harm, reason) at a military leverage; nothing to say at none."""
    if leverage <= 0.0:
        return 1.0, None
    share = relief_cap * leverage
    return (1.0 - share), ("an army and treasury the state can call on (military strength %d%%)" % round(leverage * 100))
