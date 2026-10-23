"""Whether a node's win condition is met by a measured value."""


def win_condition_met(win_condition, value):
    """True when `value` stands on the right side of the condition's target for its comparison ("<=" or ">=");
    any other comparison is never met."""
    comparison_op, target = win_condition["op"], win_condition["value"]
    if comparison_op == ">=":
        return value >= target
    if comparison_op == "<=":
        return value <= target
    return False
