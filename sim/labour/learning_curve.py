"""A learning curve on cumulative output (Complaint 644): the labour a unit takes falls by a fixed share with every
doubling of the cumulative units a trade has made, down to a floor the technique's physics sets (Wright 1936; the
plateau form y = max(K x^n, K0) is on the Wikipedia 'Learning curve' page, opened). The curve is for any actor and any
trade: the caller keeps the cumulative output per (trade, actor or community) and hands it in. It is not tuned to a
historical productivity: Thompson's Liberty-ship study found capital deepening and quality change behind much of what
looked like learning, so the rate is a per-industry range, not a constant of nature.

Plain functions of numbers.
"""
import math

from sim.constants import declare

LEARNING_RATE = declare(
    "LEARNING_RATE", 0.8, kind="engineering_estimate", unit="ratio of unit time after a doubling of cumulative output",
    source="Wright 1936 (aircraft, about 80 per cent, i.e. 20 per cent less per doubling), as stated on en.wikipedia.org/wiki/"
           "Learning_curve (opened); Thompson, working paper econwpa 9712001 (opened) summarises shipbuilding studies at 12 to "
           "24 per cent less per doubling.",
    confidence="C",
    why="The default progress ratio where a trade or technique states none. Industries differ (12 to 24 per cent less per "
        "doubling in shipbuilding), so a technique's own ratio overrides it.")


def learning_exponent(learning_rate: float) -> float:
    """The exponent of Wright's law, cost = first_unit_cost * cumulative_units ** exponent: log of the progress ratio over log of two (negative for a ratio under one)."""
    if not 0.0 < learning_rate <= 1.0:
        raise ValueError("a progress ratio is in (0, 1]: %r" % (learning_rate,))
    return math.log(learning_rate) / math.log(2.0)


def unit_time_ratio(cumulative_units: float, floor: float, learning_rate: float = LEARNING_RATE) -> float:
    """Time the next unit takes as a share of the first unit's: x^n, no lower than `floor` (the share of the first
    unit's time the technique cannot go below: the physical minimum over the first attempt's time). A trade that has made
    less than one unit is at its first unit's time. `floor` must be positive: a floor of zero would let a trade
    make output with no labour."""
    if floor <= 0.0 or floor > 1.0:
        raise ValueError("the floor is a share of the first unit's time, in (0, 1]: %r" % (floor,))
    units = max(1.0, cumulative_units)
    return max(floor, units ** learning_exponent(learning_rate))


def proficiency(cumulative_units: float, floor: float, learning_rate: float = LEARNING_RATE) -> float:
    """Output per hour as a share of the output per hour at the floor, from 'floor' (a first attempt) up to one."""
    return floor / unit_time_ratio(cumulative_units, floor, learning_rate)


def cumulative_for_proficiency(target: float, floor: float, learning_rate: float = LEARNING_RATE) -> float:
    """Units a trade must have made to reach proficiency `target` (in (floor, 1]); the inverse of `proficiency`. One for
    a target at or below a first attempt's; the units at which the floor is reached for a target of one."""
    target = min(1.0, target)
    if target <= floor:
        return 1.0
    return (floor / target) ** (1.0 / learning_exponent(learning_rate))


def error_share(proficiency_now: float, error_at_first: float, error_at_competence: float) -> float:
    """Share of output spoilt: from `error_at_first` for a first attempt to `error_at_competence` (the physical floor,
    above zero) at full proficiency, linear in proficiency. Spoilage is separate from speed because speed gains can
    come with capital deepening and a quality loss (Thompson), not from learning alone."""
    if error_at_competence <= 0.0:
        raise ValueError("the error at competence has a floor above zero: %r" % (error_at_competence,))
    level = max(0.0, min(1.0, proficiency_now))
    return error_at_first + (error_at_competence - error_at_first) * level


def pooled_units(own_units: float, others_units: float, spillover: float) -> float:
    """Cumulative units an actor learns from: its own plus a share of what others in the trade have made (Thornton and
    Thompson: spillovers across yards could exceed a yard's own learning). `spillover` is in [0, 1]."""
    return max(0.0, own_units) + max(0.0, min(1.0, spillover)) * max(0.0, others_units)
