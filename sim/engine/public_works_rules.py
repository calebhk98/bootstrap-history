"""Rules of the public works as plain functions of numbers: grain handed out, the lit working day
(Complaint 190, 640)."""


def extra_lit_hours(works):
    """Hours a day that lit works add: `works` are (extra hours a day, share of the people covered)."""
    total = 0.0
    for hours, share in works:
        total += hours * share
    return total


def working_hours_per_year(convention_hours, extra_hours_per_day, base_day_hours):
    """Hours one person gives in a year: the convention stretched in proportion to the lit hours added to a day."""
    return convention_hours * (1.0 + extra_hours_per_day / base_day_hours)

