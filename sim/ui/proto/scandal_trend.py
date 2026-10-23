"""Which way scandal is going, for the `state` reply."""


def years_until_scandal_crosses_the_line(scandal, scandal_last_year, danger):
    """Whole years until the scandal reaches the danger line at last year's pace, or None when it is not rising
    by more than a trace, is already over the line, or has no earlier reading to compare with (a one-off jump is a
    rise like any other; the caller decides whether to show it)."""
    if scandal_last_year is None or scandal - scandal_last_year <= 0.05 or scandal >= danger:
        return None
    return int(max(0.0, danger - scandal) / (scandal - scandal_last_year)) + 1
