"""How a trade the founder taught becomes a trade the society has: the years it takes and what each year does."""

RECORD_INTRODUCTION = "record_introduction"
GROW = "grow"
BECOME_ENDEMIC = "become_endemic"
WAIT = "wait"


def absorption_years(schooling_flow, minimum_years, base_years):
    """Years until a taught trade is the society's own: the base span shortened by schooling flow, never below
    one working lifetime."""
    return max(minimum_years, base_years / (1.0 + schooling_flow) ** 0.5)


def absorption_step(introduced_year, endemic, schooling_flow, year, years_needed):
    """What a year does to one taught trade. The first year it is seen is recorded as its introduction; an endemic
    trade grows; with no schooling, or before the years are up, it waits; once they are up it becomes endemic.
    `years_needed` is a callable of the schooling flow."""
    if introduced_year is None:
        return RECORD_INTRODUCTION
    if endemic:
        return GROW
    if schooling_flow <= 0.0:
        return WAIT
    if year - introduced_year >= years_needed(schooling_flow):
        return BECOME_ENDEMIC
    return WAIT


def headcount_toward_ceiling(have, ceiling, approach_rate):
    """The headcount after a year's drift toward the ceiling: the fraction of the remaining room closed. A ceiling
    that is infinite, or room of a millionth of a person or less, changes nothing."""
    if not ceiling < float("inf"):
        return have
    room = ceiling - have
    if room <= 1e-6:
        return have
    return have + room * approach_rate
