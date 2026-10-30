"""Plain rules for what the founder's military work is worth to a patron, called with figures."""
import math


def leverage_of(military_node_count, saturates_at):
    """0..1: none for no founder-built military nodes, square-root scaled, full at `saturates_at` of them."""
    if military_node_count <= 0:
        return 0.0
    return min(1.0, math.sqrt(military_node_count / saturates_at))

