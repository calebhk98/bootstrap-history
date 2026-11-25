"""Whether the hidden spin-up's first stage stops on its first quiet year (the rule sets' `spin_up_stops_early`).
Stopping early saves the years a settled economy does not need; an economy that is quiet for one year and moves
again the next then opens wherever that year left it, and the path a game runs is not the one
`spin-up-trace --stages` replays (which runs the stage to its bound). A stage that runs to its bound also says how
long that bound is (the rule sets' `spin_up_first_stage_years`)."""
from sim.constants import declare



FIRST_STAGE_YEARS_TO_REST = declare(
    "FIRST_STAGE_YEARS_TO_REST", 55, kind="temporary_heuristic", unit="years", source=None, confidence="D",
    retire="Complaints/473: an opening whose rough plan starts near its rest needs fewer hidden years",
    why="A first stage that runs to its bound has to be long enough for the economy to come to rest from the rough "
        "plan. With the coin stock level in the hidden years (spin_up_coin.py) the price level keeps rising for about "
        "this long before it holds; measured on the eight-member ensemble of England "
        "(spin-up-trace --stages --ensemble 8), where a stage of the declared bound ends with the price level still "
        "moving. Not fitted beyond that comparison.")


def the_declared_bound(declared_years: int) -> int:
    """The first stage runs at most its declared bound (sim/markets/spin_up.py)."""
    return declared_years


def long_enough_to_rest(declared_years: int) -> int:
    """The first stage runs at least `FIRST_STAGE_YEARS_TO_REST`, and its declared bound where that is longer."""
    return max(declared_years, int(FIRST_STAGE_YEARS_TO_REST))


def on_a_quiet_year() -> bool:
    """The first stage ends with the first year in which the price level, the rate and the watched prices are quiet."""
    return True


def at_its_bound() -> bool:
    """The first stage runs its full length."""
    return False
