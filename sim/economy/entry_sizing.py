"""How big a newcomer builds. A founder looks at the gap buyers left, but does not build a works far bigger
than the trade he can see in that good's market, nor one his inputs' and plant goods' markets could not
supply: a smelter planned for twenty runs that can buy a few kilograms of clay never gets its plant. Where
a market carried nothing last year there is no trade to see, and the newcomer starts on a small trial
share of the gap. What the size leaves out is not stored: the gap is still there next year and is sized
again, against a market that has grown with the newcomer's own orders."""
import math
from typing import Callable, Mapping, Optional

from sim.constants import declare

from .types import GoodId, Recipe, TileId

ENTRY_SHARE_OF_TRADED_VOLUME = declare(
    "ENTRY_SHARE_OF_TRADED_VOLUME", 0.5, kind="temporary_heuristic",
    unit="share of last year's traded volume of its good a new maker is built for", source=None, confidence="D",
    why="A newcomer adds to a market whose size it can see and expects its rivals' and the buyers' "
        "reactions to take part of the gain back. How large a share founders dared is not measured; "
        "further growth follows the producer's own expansion rule.")
ENTRY_SHARE_OF_INPUT_VOLUME = declare(
    "ENTRY_SHARE_OF_INPUT_VOLUME", 0.5, kind="temporary_heuristic",
    unit="share of last year's traded volume of an input or plant good a new maker may count on buying",
    source=None, confidence="D",
    why="Existing buyers keep their suppliers, so a newcomer can count on part of what an input market "
        "carried, not on all of it. Sellers' willingness to supply a new buyer is not modelled beyond "
        "last year's trade.")
ENTRY_SHARE_OF_UNTRADED_DEMAND = declare(
    "ENTRY_SHARE_OF_UNTRADED_DEMAND", 0.05, kind="temporary_heuristic",
    unit="share of the visible gap a new maker is built for where its market, or an input's, traded nothing",
    source=None, confidence="D",
    why="With no trade to see a founder starts on a trial scale, small enough to lose; the size that "
        "buyers' unfilled bids would really support at a price makers could meet is not derived.")

# volume traded last year of a good on a tile's market; None where the good has no market
Traded = Callable[[GoodId, TileId], Optional[float]]


def _runs_supported(volume: Optional[float], per_run: float, trial_runs: float) -> float:
    """Runs a market's trade could feed or absorb: a share of its volume, the trial size where it traded
    nothing, no limit where the good is not traded at all."""
    if volume is None or per_run <= 0.0:
        return math.inf
    return ENTRY_SHARE_OF_INPUT_VOLUME * volume / per_run if volume > 0.0 else trial_runs


def sized_runs(recipe: Recipe, good: GoodId, runs_by_gap: float, whole_gap_runs: float, tile: TileId,
               traded: Optional[Traded]) -> float:
    """Yearly runs to build: the share of the gap, held to what the good's market traded and to what the
    markets of the recipe's inputs and plant goods carried."""
    if traded is None:
        return runs_by_gap
    trial_runs = ENTRY_SHARE_OF_UNTRADED_DEMAND * whole_gap_runs
    volume = traded(good, tile)
    if volume is None:
        market_runs = math.inf
    elif volume > 0.0:
        market_runs = ENTRY_SHARE_OF_TRADED_VOLUME * volume / recipe.outputs[good]
    else:
        market_runs = trial_runs
    supply_runs = min((_runs_supported(traded(input_good, tile), per_run, trial_runs)
                       for needs in (recipe.inputs, recipe.plant_goods) for input_good, per_run in needs.items()),
                      default=math.inf)
    return min(runs_by_gap, market_runs, supply_runs)
