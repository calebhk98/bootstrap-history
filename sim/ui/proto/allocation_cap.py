"""`allocate ... useful`: an order capped at the hours a project can use."""


def capped_to_useful(hours, useful, cap_wanted):
    """(hours to set, hours originally asked or None). Without the option the order is taken as given; with it the
    order never exceeds the useful hours."""
    if cap_wanted and hours > useful:
        return useful, hours
    return hours, None
