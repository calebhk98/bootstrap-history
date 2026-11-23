"""Whether the hidden spin-up's first stage stops on its first quiet year (the rule sets' `spin_up_stops_early`).
Stopping early saves the years a settled economy does not need; an economy that is quiet for one year and moves
again the next then opens wherever that year left it, and the path a game runs is not the one
`spin-up-trace --stages` replays (which runs the stage to its bound)."""


def on_a_quiet_year() -> bool:
    """The first stage ends with the first year in which the price level, the rate and the watched prices are quiet."""
    return True


def at_its_bound() -> bool:
    """The first stage runs its full length."""
    return False
