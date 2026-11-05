"""The chance a worker who leaves his trade for the unskilled one is hired at its wage (clearing.unskilled_option)."""


def hire_chance(hours_wanted: float, hours_offered: float, hours_competing: float) -> float:
    """The chance a worker who switches to the unskilled trade is hired at its wage: the hours its employers want,
    over all the hours that seek them (the trade's own hands' offered hours and the switching trade's), at most one.
    One where the offered hours already fill the wanted ones: the market is supplied and the wage is what its hands ask."""
    if hours_wanted <= hours_offered:
        return 1.0
    return min(1.0, hours_wanted / (hours_offered + hours_competing))
