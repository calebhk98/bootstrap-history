"""Rules of the public works as plain functions of numbers: the state's consent, grain handed out, the lit working day
and the schools that teach (Complaint 190, 640)."""


def legitimacy_share(summed_effects, floor, ceiling):
    """The share of its reach the people's consent leaves the state: the works' effects summed, held between the floor
    (force and habit still collect something) and the ceiling (no praise makes a state stronger than that)."""
    return max(floor, min(ceiling, summed_effects))


def extra_lit_hours(works):
    """Hours a day that lit works add: `works` are (extra hours a day, share of the people covered)."""
    total = 0.0
    for hours, share in works:
        total += hours * share
    return total


def working_hours_per_year(convention_hours, extra_hours_per_day, base_day_hours):
    """Hours one person gives in a year: the convention stretched in proportion to the lit hours added to a day."""
    return convention_hours * (1.0 + extra_hours_per_day / base_day_hours)


def schooling_flow(schools, field, required_school_shut):
    """Teaching flow of the open schools: `schools` are (value, fields the school reaches or None for all of them).
    Nothing when a school the others depend on is shut; with a `field`, only the schools that reach it count."""
    if required_school_shut:
        return 0.0
    if field is None:
        return sum(value for value, _reaches in schools)
    return sum(value for value, reaches in schools if reaches is None or field in reaches)


def printing_boosted_flow(flow, boost, diffusion):
    """The flow once diffused printing is counted: texts make the same effort teach faster, but a flow of zero stays zero."""
    if flow <= 0.0:
        return 0.0
    return flow * (1.0 + boost * diffusion)
