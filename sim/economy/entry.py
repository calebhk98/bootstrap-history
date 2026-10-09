"""New makers. Where buyers wanted more of a good than was sold last year, a way of making it that the
society knows (the setup's recipes), and that pays at the price buyers bid, starts a producer on the
market's main tile, for the part of the gap its makers' idle capacity could not have met (newcomers to
a recipe already worked there join that producer: a workshop with no plant cannot otherwise grow). It starts at a
share of that gap, with its owner's stake as working cash
and a loan for its plant through the credit market, like any expansion.

Placement is location.py's: the tile of the market area where a run costs least and idle hands can
staff it, within the limits a site imposes (sites.py). Without a siting it is the market's anchor tile.
"""
import math
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from sim.constants import declare

from . import unit_cost
from .entry_sizing import Traded, sized_runs
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


CLOSED_CAPACITY_SHARE_OF_PAST_SCALE = declare(
    "CLOSED_CAPACITY_SHARE_OF_PAST_SCALE", 0.01, kind="temporary_heuristic",
    unit="share of the runs a producer last worked or expected to sell", source=None, confidence="D",
    why="Capacity decays geometrically and never reaches nothing, so a producer is closed once what is "
        "left is a sliver of its own past scale; the sliver stands for a workshop too small to keep open.")


def producers_to_close(producers: Mapping[str, Producer], pending, debtors) -> List[str]:
    """Producers whose capacity is a negligible share of the scale they once worked, with no plant on the
    way and no debt: a newcomer whose plant was never funded or a maker that dwindled. They close and
    hand what they hold to their owner."""
    return [agent_id for agent_id, producer in sorted(producers.items())
            if producer.capacity_runs <= CLOSED_CAPACITY_SHARE_OF_PAST_SCALE * max(
                producer.last_runs, producer.expected_sales, 0.0)
            and agent_id not in pending and agent_id not in debtors]


def gap_beyond_spare(unmet: float, spare_output: float) -> float:
    """The part of a market's unmet demand its makers could not have met from idle capacity."""
    return max(0.0, unmet - max(0.0, spare_output))


def entry_plans(recipes: Mapping[str, Recipe], view: MarketView,
                unmet: Mapping[Tuple[GoodId, AreaId], UnmetDemand],
                rent_by_tile: Optional[Mapping[TileId, float]] = None,
                land_per_run: Optional[Mapping[str, float]] = None,
                traded: Optional[Traded] = None, siting=None) -> List[EntryPlan]:
    """New makers for each market with unmet demand: the known recipes making the good, best return on
    capital at last year's prices first, each that beats the interest rate, each built for a share of what
    the better ones leave of the gap (no limit on how many a year: the gap and the returns decide). Rent per
    hectare last year on the tile, times the land a run takes, is part of a run's cost. With `traded`,
    the size is held to the trade the market and its suppliers' markets carried (entry_sizing.py), and
    a recipe whose size comes to nothing gives way to the next best. With `siting` (location.py) a newcomer
    goes to the tile that suits it, else to the market's anchor."""
    rent_by_tile, land_per_run = rent_by_tile or {}, land_per_run or {}
    makers: Dict[GoodId, List[str]] = {}
    for recipe_id in sorted(recipes):
        for good in recipes[recipe_id].outputs:
            makers.setdefault(good, []).append(recipe_id)
    plans = []
    for key in sorted(unmet):
        demand = unmet[key]
        if demand.quantity <= 0.0:
            continue
        currency = view.currency_of(demand.area)
        ranked = []
        for recipe_id in makers.get(demand.good, ()):
            rent = rent_by_tile.get(demand.anchor_tile, 0.0) * land_per_run.get(recipe_id, 0.0)
            yearly_return = _return_at(recipes[recipe_id], recipe_id, demand.anchor_tile, view, rent)
            if yearly_return > view.interest_rate(currency):
                ranked.append((-yearly_return, recipe_id))
        remaining = demand.quantity
        for negative_return, recipe_id in sorted(ranked):
            recipe = recipes[recipe_id]
            if remaining <= 0.0:
                break
            whole_gap_runs = remaining / recipe.outputs[demand.good]
            tile = demand.anchor_tile
            runs = sized_runs(recipe, demand.good, whole_gap_runs * ENTRY_SHARE_OF_UNMET_DEMAND, whole_gap_runs,
                              tile, traded)
            if siting is not None and runs > 0.0 and math.isfinite(runs):
                picked = siting(recipe_id, UnmetDemand(demand.good, demand.area, demand.anchor_tile, remaining), runs)
                if picked is None:
                    continue
                tile, runs = picked
            if runs > 0.0 and math.isfinite(runs):
                plans.append(EntryPlan(recipe_id, tile, demand.good, runs, -negative_return))
                remaining -= runs * recipe.outputs[demand.good]
    return plans


def _return_at(recipe: Recipe, recipe_id: str, tile: TileId, view: MarketView, rent: float = 0.0) -> float:
    probe = Producer("probe", "probe", recipe_id, tile, 1.0)
    outputs = expected_output_prices(probe, recipe, view) or {}
    return unit_cost.return_on_capital(recipe, outputs, live_input_prices(probe, recipe, view),
                                       live_wages(probe, recipe, view), rent)
