"""When a civilisation's hazards land, and which ones are still ahead.

ONE PLACE, BECAUSE IT WAS TWO AND THEY WERE DRIFTING.

`FogMixin.knowledge_risk` and `SocietyMixin.hazard_timeline` each opened
`civ["hazards"]`, read the `years` list, widened a one-element list into a
start and an end, and skipped anything the player had already lived past.
The two copies were identical apart from the name of the list they were
filling, which is the shape a bug hides in: a fix to the window arithmetic
in one screen leaves the other screen quoting the old answer, and the two
disagree about the same hazard on the same turn with nothing in either file
to say the other exists.

The window arithmetic is the whole of what they shared, so that is the whole
of what moved. Each caller still builds its own row - the fog screen wants
sack chances and hedges, the society screen wants relief and lead times -
and those have never been the same thing.
"""


from typing import Any, Dict, Iterator, Tuple


def hazards_not_yet_past(
        civilization: Dict[str, Any],
        current_year: int) -> Iterator[Tuple[Dict[str, Any], int, int, bool]]:
    """Yield every hazard whose window has not closed, oldest window first.

    Yields `(hazard, year_start, year_end, in_progress)` for each hazard in
    `civilization["hazards"]` that carries a usable `years` entry and has not
    already finished.

    A `years` list of one element means a hazard that lands and ends in the
    same year, so the end is the start. `in_progress` is true when the
    current year sits inside the window, which the callers use to choose
    between "this is happening" and "this is coming".

    A hazard with no `years` at all is skipped rather than defaulted: a
    hazard with no date is not a hazard scheduled for year zero, and guessing
    one would put an imaginary crisis at the top of a player's screen.
    """
    for hazard in (civilization.get("hazards") or []):
        years = hazard.get("years") or []
        if not years:
            continue
        year_start = years[0]
        year_end = years[1] if len(years) > 1 else years[0]
        if current_year > year_end:
            continue                      # already survived, or missed
        yield hazard, year_start, year_end, year_start <= current_year <= year_end
