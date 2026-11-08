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

import numpy as np
from sim.constants import declare

from . import entry_practice, market_quote, unit_cost
from .entry_sizing import Traded, sized_runs
from .goods_market import quantity_at
from .producer_store import ProducerStore
from .producers import Producer, expected_output_prices, live_input_prices, live_wages
from .protocols import MarketView
from .types import AreaId, Bid, ClearingResult, GoodId, Offer, Recipe, TileId

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


def wanted_in_round(bids: Sequence[Bid], offers: Sequence[Offer], result: ClearingResult) -> float:
    """What a round's buyers asked for: at the asks they faced when it traded (`result.demand_at_price`); when it
    traded nothing, at the lowest ask on offer, or with no ask at the highest ceiling any bid names (0 when none)."""
    if result.quantity > 0.0:
        return result.demand_at_price
    price = market_quote.lowest_unfilled_ask(offers)
    if price is None:
        price = market_quote.best_unfilled_bid(bids)
    if price is None:
        return 0.0
    return math.fsum(quantity_at(bid, price) for bid in bids)


def unmet_quantity(wanted: float, delivered: float) -> float:
    """What buyers asked for beyond what was delivered, both counted over the same rounds."""
    return max(0.0, wanted - delivered)


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
    if isinstance(producers, ProducerStore):
        order = producers.order()
        table = producers.table
        small = table.capacity_runs[order] <= CLOSED_CAPACITY_SHARE_OF_PAST_SCALE * np.maximum(
            np.maximum(table.last_runs[order], table.expected_sales[order]), 0.0)
        return [agent_id for agent_id in (producers.ids[row] for row in order[small].tolist())
                if agent_id not in pending and agent_id not in debtors]
    return [agent_id for agent_id, producer in sorted(producers.items())
            if producer.capacity_runs <= CLOSED_CAPACITY_SHARE_OF_PAST_SCALE * max(
                producer.last_runs, producer.expected_sales, 0.0)
            and agent_id not in pending and agent_id not in debtors]


def gap_beyond_spare(unmet: float, spare_output: float) -> float:
    """The part of a market's unmet demand its makers could not have met from idle capacity."""
    return max(0.0, unmet - max(0.0, spare_output))


def entry_plans(recipes: Mapping[str, Recipe], view: MarketView,
                unmet: Mapping[Tuple[GoodId, AreaId], UnmetDemand],
                traded: Optional[Traded] = None, siting=None, unfilled=None, rent_of=None,
                crews_of: Optional[entry_practice.CrewsOf] = None, costs=None) -> List[EntryPlan]:
    """New makers for each market with unmet demand: the known recipes making the good, best return on
    capital at last year's prices first, each that beats the interest rate after the plant's wear, each built for a share of what
    the better ones leave of the gap (no limit on how many a year: the gap and the returns decide). With `traded`,
    the size is held to the trade the market and its suppliers' markets carried (entry_sizing.py), and
    a recipe whose size comes to nothing gives way to the next best. With `siting` (location.py) a newcomer
    goes to the tile that suits it, else to the market's anchor. With `unfilled` (entry_backed.py) the bids left
    unfilled at the recipe's full cost count with the trade. With `rent_of(recipe_id, tile)` a newcomer's rent is what its own use pays there
    (entrant_rent.py); without it a run pays no rent. With `crews_of` (entry_practice.py) a recipe's return is judged on the hours
    its newcomer will need over the years it is judged on (starting at its peers' practice, learning on the runs it is built
    for), not the booked hours. With `costs` (entry_tables.EntryTables) every recipe's return is read from the year's arrays at its
    newcomer's planned hours and the rent its site asks, in place of `rent_of` and `crews_of`."""
    makers: Dict[GoodId, List[str]] = {}
    for recipe_id in sorted(recipes):
        for good in recipes[recipe_id].outputs:
            makers.setdefault(good, []).append(recipe_id)
    plans = []
    markets = []        # (demand, the rate of its currency, the recipes making its good, where its pairs start in `requests`)
    requests = []       # (recipe id, tile, runs the entrant is planned on, rate) for each recipe of each market
    for key in sorted(unmet):
        demand = unmet[key]
        if demand.quantity <= 0.0:
            continue
        market_rate = view.interest_rate(view.currency_of(demand.area))
        candidates = makers.get(demand.good, ()) if market_rate is not None else ()
        markets.append((demand, market_rate, candidates, len(requests)))
        if costs is not None:
            requests.extend((recipe_id, demand.anchor_tile,
                             demand.quantity / recipes[recipe_id].outputs[demand.good] * ENTRY_SHARE_OF_UNMET_DEMAND, market_rate)
                            for recipe_id in candidates)
    returns = costs.returns_many(requests) if costs is not None else None
    for demand, market_rate, candidates, first_request in markets:
        ranked = []
        for position, recipe_id in enumerate(candidates):
            if returns is not None:
                yearly_return, after_recovery = returns[first_request + position]
            else:
                rent = rent_of(recipe_id, demand.anchor_tile) if rent_of is not None else 0.0
                planned = recipes[recipe_id]
                if crews_of is not None:
                    share_runs = demand.quantity / planned.outputs[demand.good] * ENTRY_SHARE_OF_UNMET_DEMAND
                    planned = entry_practice.planned_recipe(planned, crews_of(recipe_id), share_runs)
                yearly_return, after_recovery = _returns_at(planned, recipe_id, demand.anchor_tile, view, market_rate, rent)
            if yearly_return is not None and after_recovery is not None and after_recovery > market_rate:
                ranked.append((-yearly_return, recipe_id))
        remaining = demand.quantity
        for negative_return, recipe_id in sorted(ranked):
            recipe = recipes[recipe_id]
            if remaining <= 0.0:
                break
            whole_gap_runs = remaining / recipe.outputs[demand.good]
            tile = demand.anchor_tile
            backed = unfilled(recipe_id, demand.good, tile, whole_gap_runs * ENTRY_SHARE_OF_UNMET_DEMAND * recipe.outputs[demand.good]) if unfilled is not None and traded is not None else 0.0
            runs = sized_runs(recipe, demand.good, whole_gap_runs * ENTRY_SHARE_OF_UNMET_DEMAND, whole_gap_runs,
                              tile, traded, unfilled=backed)
            if siting is not None and runs > 0.0 and math.isfinite(runs):
                picked = siting(recipe_id, UnmetDemand(demand.good, demand.area, demand.anchor_tile, remaining), runs)
                if picked is None:
                    continue
                runs = sized_runs(recipe, demand.good, picked[1], whole_gap_runs, demand.anchor_tile, traded, picked[0], backed)
                tile = picked[0]
            if runs > 0.0 and math.isfinite(runs):
                plans.append(EntryPlan(recipe_id, tile, demand.good, runs, -negative_return))
                remaining -= runs * recipe.outputs[demand.good]
    return plans


def _returns_at(recipe: Recipe, recipe_id: str, tile: TileId, view: MarketView, market_rate: float,
                rent: float = 0.0) -> Tuple[Optional[float], Optional[float]]:
    """A newcomer's yearly return on the recipe at the tile (gross, which the plant loan is priced from) and the same
    after the plant's wear at `market_rate` (which it must beat to enter)."""
    probe = Producer("probe", "probe", recipe_id, tile, 1.0)
    outputs = expected_output_prices(probe, recipe, view) or {}
    inputs, wages = live_input_prices(probe, recipe, view), live_wages(probe, recipe, view)
    return (unit_cost.return_on_capital(recipe, outputs, inputs, wages, rent),
            unit_cost.return_after_recovery(recipe, outputs, inputs, wages, market_rate, rent))
