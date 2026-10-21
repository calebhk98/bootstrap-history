"""What idle plantless capacity loses in a year: the tools its workers would have worn, over their service life.
A recipe with no tool wear has nothing that idles into disrepair (its hands are hired, and leave only through the
labour market), so it loses nothing here; whether its workplaces shut is decided by whether they cover running cost
(`producers_close.close_year`). Nothing here names a good or a trade."""
import math
from typing import Mapping

from .types import GoodId, Recipe


def wear_share_per_year(recipe: Recipe, service_lives: Mapping[GoodId, float]) -> float:
    """The share of idle capacity that falls out of use in a year: the recipe's tools' yearly wear (one over a
    tool's service life), weighted by how much of each a run wears. A tool of no known life, or used up within
    the year, does not count."""
    weight = lived = 0.0
    for good, per_run in recipe.tool_wear.items():
        life = service_lives.get(good, 0.0)
        if per_run > 0.0 and life > 0.0 and math.isfinite(life):
            weight += per_run
            lived += per_run / life
    return min(1.0, lived / weight) if weight > 0.0 else 0.0
