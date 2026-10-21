"""The yearly staff phase's hiring rules, on values given: whether a household may take on people and how it moves
by whole people toward a target. (Who is let go when the payroll cannot be met is `payroll_trim`, the replacement of a
taught trade `staff_replacement`, the scholar target `sim/labour/staff_targets.py`.)"""


def has_room_to_hire(capital, credit_limit, credit_room_share):
    """Whether a household may take on people: it is in funds, or in arrears by no more than the share of its credit
    line that hiring may draw. Being overdrawn alone is not a bar."""
    return capital >= 0 or -capital <= credit_limit * credit_room_share


def hires_needed(have, wanted_whole):
    """Whole people to take on (positive) or release (negative) so `have` reaches `wanted_whole`; changes of less
    than a whole person are not acted on."""
    delta = wanted_whole - have
    if delta >= 1.0:
        return int(delta)
    if delta <= -1.0:
        return -int(-delta)
    return 0
