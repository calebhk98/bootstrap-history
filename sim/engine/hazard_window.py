"""When a civilisation's hazards land, and which ones are still ahead.

ONE PLACE, NOT TWO. `FogMixin.knowledge_risk` and `SocietyMixin.hazard_timeline`
each need to open `civ["hazards"]`, read the `years` list, widen a
one-element list into a start and an end, and skip anything the player
has already lived past - identical window arithmetic apart from the name
of the list being filled. Duplicating it is the shape a bug hides in: a
fix to the window arithmetic in one screen would leave the other screen
quoting the old answer, and the two would disagree about the same hazard
on the same turn with nothing in either file to say the other exists.
This module is the one place that arithmetic lives.

The window arithmetic is the whole of what the two callers share, so that
is the whole of what moved here. Each caller still builds its own row -
the fog screen wants sack chances and hedges, the society screen wants
relief and lead times - and those are not the same thing.
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
