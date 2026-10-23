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


def approach(current, target, rate):
    """`current` moved the share `rate` of the way to `target`."""
    return current + (target - current) * rate


def craft_headcount(desired_artisans, freedmen, slaves, slave_craft_credit):
    """Craftsmen the artisan target asks the household to pay for: the target less the freedmen already counted in it and
    the share of the slaves who do craft work; never below nothing."""
    return max(0.0, desired_artisans - freedmen - slaves * slave_craft_credit)


def artisan_goal(craft, specialists, artisans_held, closed_shortfall):
    """The artisans automatic hiring aims at: the craft headcount less what taught specialists already cover (never under a
    quarter of it, so specialists cannot squeeze the generic artisans away), or what is held plus the hands shut concerns lack."""
    return max(craft * 0.25, craft - specialists, artisans_held + closed_shortfall)


def scholar_goal(desired_scholars, scholars_held, closed_shortfall):
    """The scholars automatic hiring aims at: the smoothed target, or what is held plus the hands shut concerns lack."""
    return max(desired_scholars, scholars_held + closed_shortfall)


def directors_next(directors, capacity, approach_rate, attrition_rate):
    """Deputies directing work next year: they approach what the institutions allow and are lost at the attrition rate,
    never below nothing."""
    return max(0.0, directors + ((capacity - directors) * approach_rate - directors * attrition_rate))


def can_afford_replacement(capital, annual_wage, years_of_wage):
    """Whether the household holds more than the wage of a replacement for the years it must be able to carry him."""
    return capital > annual_wage * years_of_wage
