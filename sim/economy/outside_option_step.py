"""How far what a worker must earn moves in a year (the rule sets' `outside_option_stepped`). The outside option is
what the floors of a worker's household cost at the tile's offered prices (`year_labour.outside_option_by_tile`), and a
worker asks no less for a year. A good that serves a floor can drop out of offer for a year; the need is then read at
a dearer good's quote, which in a market with next to nothing on offer may stand at many times what anything trades
for. The cost of the floors on the tile jumps many-fold, the asks with it, and the tile's hours go unhired at the going
wage. Where the figure is stepped it moves from last year's by no more than a market's price may move in a year
(`price_step.within_a_years_move`): a year's gap in what is on offer is one step, and a change that lasts still
arrives."""
from typing import Dict, Mapping

from . import price_step


def as_priced(_last_year: Mapping[str, float], this_year: Mapping[str, float]) -> Dict[str, float]:
    """This year's cost of the floors by tile, as priced."""
    return dict(this_year)


def within_a_years_move(last_year: Mapping[str, float], this_year: Mapping[str, float]) -> Dict[str, float]:
    """This year's cost of the floors by tile, each held within a year's price move of the tile's figure last year; a
    tile with no figure last year takes this year's."""
    return {tile: price_step.within_a_years_move(cost, last_year.get(tile)) for tile, cost in this_year.items()}
