"""A need met to its satiation limit stops asking for more as its price falls.

A household's units of a need are its floor plus its surplus spending over the need's price, capped at the need's
satiation limit (`sim/world/need_satiation.py`). The bid schedule extends that rule along the price axis: the flexible
units of a satiated need do not grow when the price falls (a household already eating to its limit takes no more of a
cheaper grain), and the bid budget, which was sized at the capped units, holds the units down when the price rises. So the
schedule is the capped rule, not an uncapped power law that overshoots the limit in a glut."""
from sim.jit import njit

NO_RESPONSE_TO_PRICE = 0.0       # elasticity of a bid whose flexible units are at the satiation limit


@njit
def is_satiated(total_units, limit_per_person, people):
    """Whether a need's units for `people` sit at its satiation limit (`limit_per_person` is NaN for a need with none)."""
    return limit_per_person == limit_per_person and total_units >= limit_per_person * people


@njit
def bid_elasticity(substitution, satiated):
    """The elasticity of a bid's flexible units: the basket's substitution, or none when the need is satiated."""
    return NO_RESPONSE_TO_PRICE if satiated else substitution
