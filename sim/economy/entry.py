"""New makers. Where buyers wanted more of a good than was sold last year, a way of making it that the
society knows (the setup's recipes), and that pays at the price buyers bid, starts a producer on the
market's main tile, for the part of the gap its makers' idle capacity could not have met (newcomers to
a recipe already worked there join that producer: a workshop with no plant cannot otherwise grow). It starts at a
share of that gap, with its owner's stake as working cash
and a loan for its plant through the credit market, like any expansion.

Placement follows the opening: the market area's anchor tile. Whether a tile suits a recipe (a
deposit, a climate) is not modelled here; the recipes are already only those the society can use.
"""
import math
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

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
    quantity: float                  # what buyers wanted at the year's price beyond what was sold, less spare
    bids: Tuple[Bid, ...] = ()       # the year's bids, to ask what buyers would take at a maker's cost
    sold: float = 0.0
    spare: float = 0.0               # what the market's makers could have added from idle capacity


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


def producers_to_close(producers: Mapping[str, Producer], pending, debtors) -> List[str]:
    """Producers with no capacity, no plant on the way and no debt: a newcomer whose plant was never
    funded or a maker that exited. They close and hand what they hold to their owner."""
    return [agent_id for agent_id, producer in sorted(producers.items())
            if producer.capacity_runs <= 0.0 and agent_id not in pending and agent_id not in debtors]


def gap_beyond_spare(unmet: float, spare_output: float) -> float:
    """The part of a market's unmet demand its makers could not have met from idle capacity."""
    return max(0.0, unmet - max(0.0, spare_output))


def entry_plans(recipes: Mapping[str, Recipe], view: MarketView,
                unmet: Mapping[Tuple[GoodId, AreaId], UnmetDemand],
                land_per_run: Optional[Mapping[str, float]] = None) -> List[EntryPlan]:
    """At most one new maker per market: the known recipe making the good with the best return on
    capital at last year's prices, if that return beats the interest rate. A maker on no land is built
    for what buyers would take at its own full cost beyond what was sold, at most what the market
    already trades, so a price held far above cost draws makers in; one on land only for buyers turned away at the price, until land carries a
    rent (Complaint 393). Idle capacity in the market comes off either."""
    land_per_run = land_per_run or {}
    makers: Dict[GoodId, List[str]] = {}
    for recipe_id in sorted(recipes):
        for good in recipes[recipe_id].outputs:
            makers.setdefault(good, []).append(recipe_id)
    plans = []
    for key in sorted(unmet):
        demand = unmet[key]
        best = None
        for recipe_id in makers.get(demand.good, ()):
            recipe = recipes[recipe_id]
            yearly_return = _return_at(recipe, recipe_id, demand.anchor_tile, view)
            if not yearly_return > view.interest_rate(view.currency_of(demand.area)):
                continue
            quantity = demand.quantity
            if land_per_run.get(recipe_id, 0.0) <= 0.0 and demand.bids:
                cost = _full_cost_per_unit(recipe, recipe_id, demand.good, demand.anchor_tile, view)
                if cost is not None:
                    # no more than the market already trades: entry grows a market, it does not refound it
                    at_cost = min(unmet_quantity(demand.bids, cost, demand.sold), demand.sold)
                    quantity = max(quantity, gap_beyond_spare(at_cost, demand.spare))
            if quantity > 0.0 and (best is None or yearly_return > best[0]):
                best = (yearly_return, recipe_id, quantity)
        if best is None:
            continue
        yearly_return, recipe_id, quantity = best
        runs = quantity * ENTRY_SHARE_OF_UNMET_DEMAND / recipes[recipe_id].outputs[demand.good]
        if runs > 0.0 and math.isfinite(runs):
            plans.append(EntryPlan(recipe_id, demand.anchor_tile, demand.good, runs, yearly_return))
    return plans


def _full_cost_per_unit(recipe: Recipe, recipe_id: str, good: GoodId, tile: TileId, view: MarketView
                        ) -> Optional[float]:
    """What a unit of `good` costs a new maker at live prices: the run's variable cost and plant charge,
    shared over its outputs by value; None when it cannot be priced."""
    probe = Producer("probe", "probe", recipe_id, tile, 1.0)
    inputs, wages = live_input_prices(probe, recipe, view), live_wages(probe, recipe, view)
    rate = view.interest_rate(view.currency_of(view.area_of(good, tile)))
    cost = (unit_cost.variable_cost_per_run(recipe, inputs, wages)
            + unit_cost.capital_charge_per_run(recipe, inputs, wages, rate))
    outputs = expected_output_prices(probe, recipe, view) or {}
    value = unit_cost.revenue_per_run(recipe, outputs)
    if not (math.isfinite(cost) and cost > 0.0 and value > 0.0 and outputs.get(good, 0.0) > 0.0):
        return None
    return cost * outputs[good] / value


def _return_at(recipe: Recipe, recipe_id: str, tile: TileId, view: MarketView) -> float:
    probe = Producer("probe", "probe", recipe_id, tile, 1.0)
    outputs = expected_output_prices(probe, recipe, view) or {}
    return unit_cost.return_on_capital(recipe, outputs, live_input_prices(probe, recipe, view),
                                       live_wages(probe, recipe, view))
