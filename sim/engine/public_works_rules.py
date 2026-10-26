"""Rules of the public works as plain functions of numbers: the state's consent, grain handed out, the lit working day
(Complaint 190, 640)."""


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

