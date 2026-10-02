"""New makers. Where buyers wanted more of a good than was sold last year, a way of making it that the
society knows (the setup's recipes), and that pays at the price buyers bid, starts a producer on the
market's main tile, for the part of the gap its makers' idle capacity could not have met (a second
maker of a recipe can join the first: a workshop with no plant cannot otherwise grow). It starts at a
share of that gap, with its owner's stake as working cash
and a loan for its plant through the credit market, like any expansion.

Placement follows the opening: the market area's anchor tile. Whether a tile suits a recipe (a
deposit, a climate) is not modelled here; the recipes are already only those the society can use.
"""
import math
from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence, Tuple

from sim.constants import declare

from . import unit_cost
from .goods_market import quantity_at
from .producers import Producer, expected_output_prices, live_input_prices, live_wages
from .protocols import MarketView
from .types import AreaId, Bid, GoodId, Recipe, TileId

ENTRY_SHARE_OF_UNMET_DEMAND = declare(
    "ENTRY_SHARE_OF_UNMET_DEMAND", 0.5, kind="temporary_heuristic",
    unit="share of last year's unmet demand a new maker is built for", source=None, confidence="D",
    why="A newcomer does not bet on the whole gap: others may enter and the demand may not last. How "
        "far founders trust a gap is not measured; growth after entry follows the producer's own "
        "expansion rule.")
ENTRANT_OWNER_STAKE_SHARE = declare(
    "ENTRANT_OWNER_STAKE_SHARE", 0.1, kind="temporary_heuristic",
    unit="share of the owner's cash staked as working cash", source=None, confidence="D",
    why="A household starting or keeping a workshop going risks part of its savings, not all; plant is "
        "borrowed. The share people staked is not measured for any society here.")

ENTRANT_DEBT_PER_STAKE = declare(
    "ENTRANT_DEBT_PER_STAKE", 1.0, kind="temporary_heuristic",
    unit="loan for plant per unit of the owner's stake", source=None, confidence="D",
    why="Lenders advance a newcomer about what its owner puts at risk, not its whole plant; with no "
        "stake there is no loan. Stands in for lenders' judgement of an untried venture, which is not "
        "modelled.")


@dataclass(frozen=True)
class UnmetDemand:
    good: GoodId
    area: AreaId
    anchor_tile: TileId
    quantity: float                  # what buyers wanted at the year's price beyond what was sold


@dataclass(frozen=True)
class EntryPlan:
    recipe_id: str
    tile: TileId
    good: GoodId
    runs: float                      # yearly runs of capacity it is built for
    yearly_return: float


def unmet_quantity(bids: Sequence[Bid], price: float, sold: float) -> float:
    """What buyers wanted at the year's price beyond what was sold (zero when none was priced)."""
    if price <= 0.0 or not math.isfinite(price):
        return 0.0
    wanted = math.fsum(quantity_at(bid, price) for bid in bids)
    return max(0.0, wanted - sold)


def entrant_loan(plant_value: float, owner_stake: float) -> float:
    """What lenders will advance a newcomer for its plant: the plant's value, at most its owner's stake
    times ENTRANT_DEBT_PER_STAKE."""
    return max(0.0, min(plant_value, ENTRANT_DEBT_PER_STAKE * max(0.0, owner_stake)))


def restake(shortfall: float, owner_cash: float, pays: bool) -> float:
    """What an owner puts back into its producer: up to the working cash it lacks, from the same share
    of the owner's cash a founder stakes, and only when the producer's runs pay."""
    if not pays or shortfall <= 0.0:
        return 0.0
    return min(shortfall, ENTRANT_OWNER_STAKE_SHARE * max(0.0, owner_cash))


def gap_beyond_spare(unmet: float, spare_output: float) -> float:
    """The part of a market's unmet demand its makers could not have met from idle capacity."""
    return max(0.0, unmet - max(0.0, spare_output))


def entry_plans(recipes: Mapping[str, Recipe], view: MarketView,
                unmet: Mapping[Tuple[GoodId, AreaId], UnmetDemand]) -> List[EntryPlan]:
    """At most one new maker per market with unmet demand: the known recipe making the good with the
    best return on capital at last year's prices, if that return beats the interest rate."""
    makers: Dict[GoodId, List[str]] = {}
    for recipe_id in sorted(recipes):
        for good in recipes[recipe_id].outputs:
            makers.setdefault(good, []).append(recipe_id)
    plans = []
    for key in sorted(unmet):
        demand = unmet[key]
        if demand.quantity <= 0.0:
            continue
        best = None
        for recipe_id in makers.get(demand.good, ()):
            yearly_return = _return_at(recipes[recipe_id], recipe_id, demand.anchor_tile, view)
            currency = view.currency_of(demand.area)
            if yearly_return > view.interest_rate(currency) and (best is None or yearly_return > best[0]):
                best = (yearly_return, recipe_id)
        if best is None:
            continue
        recipe = recipes[best[1]]
        runs = demand.quantity * ENTRY_SHARE_OF_UNMET_DEMAND / recipe.outputs[demand.good]
        if runs > 0.0 and math.isfinite(runs):
            plans.append(EntryPlan(best[1], demand.anchor_tile, demand.good, runs, best[0]))
    return plans


def _return_at(recipe: Recipe, recipe_id: str, tile: TileId, view: MarketView) -> float:
    probe = Producer("probe", "probe", recipe_id, tile, 1.0)
    outputs = expected_output_prices(probe, recipe, view) or {}
    return unit_cost.return_on_capital(recipe, outputs, live_input_prices(probe, recipe, view),
                                       live_wages(probe, recipe, view))
