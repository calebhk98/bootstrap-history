"""A producer is an agent that runs one recipe on one tile: it plans, produces and offers.

The year loop calls these in order (`economy.py` owns the loop; `producers_close.py` has the year's end):

    plan(producer, recipe, view, cash)            -> Plan: runs, labour bids, input bids
    produce(producer, recipe, inputs_held, hours_hired, runs_planned) -> (runs achieved, GoodsMoves)
    offers(producer, recipe, view, stock_by_good, cash_shortfall, interest_rate, specs) -> Offers
    producers_close.close_year(...); entry.py starts new producers

Planning uses EXPECTED prices (what the producer last saw, adjusted adaptively), not this year's, for
its outputs and for the inputs a run uses up, so supply follows last year's price: the cobweb lag. A
producer runs while a run's expected revenue covers its variable cost, so it shuts down below average
variable cost and may run part of its capacity when cash is short. Plant already built is sunk for the run decision; it is charged only in the year's close
and in the choice to expand or enter. Land is rented each year (land_market.py): last year's rent per run
is a variable cost and the land granted caps the runs. Deposits are not inputs: the yield factor and
capacity carry the site, so a deposit's rent shows up as profit. Nothing here names a good, trade or place.
View lookups: goods by `view.area_of(good, tile)`, labour by `view.area_of(trade, tile)`.
"""
import math
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Tuple

from sim.constants import declare

from . import ask_raise, inventory, tool_fallback, unit_cost
from .protocols import MarketView
from .types import (AgentId, Bid, EDGE_CONSUMPTION, EDGE_PRODUCTION, GoodId, GoodSpec, GoodsMove, LabourBid,
                    Offer, Recipe, TileId)
from .replaced import replaced

EXPECTATION_ADJUSTMENT_SHARE = declare(
    "EXPECTATION_ADJUSTMENT_SHARE", 0.5, kind="temporary_heuristic",
    unit="share of last year's surprise folded into the expected price", source=None, confidence="D",
    why="A producer expects next year's price from its own past, moving part of the way to what it "
        "last saw; a share of one is the naive cobweb. Real producers use forward prices, stocks and "
        "reports that the economy does not model. The share is a placeholder for that information.")
REGRESSIVE_EXPECTATION_WEIGHT = declare(
    "REGRESSIVE_EXPECTATION_WEIGHT", 0.3, kind="temporary_heuristic",
    unit="share of the gap to the break-even price closed in a producer's expectation each year",
    source=None, confidence="D",
    why="Producers who expect only last year's price chase every swing, and a chain of them feeding each "
        "other swings wider every year (the divergent cobweb). Producers also know that prices far from "
        "cost do not last; regressive expectations (Nerlove 1958) weigh that in. The weight is unmeasured.")
COST_SPREAD_WITHIN_PRODUCER = declare(
    "COST_SPREAD_WITHIN_PRODUCER", 0.3, kind="temporary_heuristic",
    unit="standard deviation of the log of unit cost across the workplaces one producer stands for",
    source=None, confidence="D",
    why="One producer agent stands for every workplace running its recipe in its market area; their "
        "sites, skills and tools differ, so as the price rises past the average cost more of them find "
        "it worth working and output rises smoothly instead of jumping from none to all. The spread "
        "could come from the spread of land fertility and deposit grade across the area's tiles.")
OUTPUT_CHANGE_SHARE_PER_YEAR = declare(
    "OUTPUT_CHANGE_SHARE_PER_YEAR", 0.25, kind="temporary_heuristic",
    unit="share of capacity a producer's yearly runs can rise or fall by", source=None, confidence="D",
    why="A workshop cannot double or halve its work in a year: hands are hired, trained and let go, "
        "and stocks of inputs built or run down, over seasons. Without a limit a producer that sees "
        "last year's price swings its whole output, and a chain of such producers feeding each other "
        "amplifies the swing every year instead of settling. A model of hiring and training would "
        "derive the speed per trade.")
STOCK_CLEARING_YEARS = declare(
    "STOCK_CLEARING_YEARS", 2.0, kind="temporary_heuristic",
    unit="years over which a producer works off stock held beyond its target", source=None, confidence="D",
    retire="Complaints/473-the-agent-economy-spin-up-never-settles-so-the-opening-is-a-point-on-a-cycle.md",
    why="Eurace firms plan output from expected sales and an inventory target (Eurace@Unibi user manual 2011, as read in "
        "Complaints/reports/research-reference-economy-models.md), and Caiani et al. 2016 (eq 3.7) move the markup with "
        "inventory, so excess stock is drawn down over a stretch of years and not in one: a producer with a positive "
        "margin whose stock clears in the stretch keeps working. The stretch itself has no source; it follows spoilage, "
        "interest and the cost of closing a workshop, which are not tied to this rule yet.")
STORAGE_COST_PER_UNIT = declare(
    "STORAGE_COST_PER_UNIT", 0.0, kind="temporary_heuristic",
    unit="money per unit of good per year", source=None, confidence="D",
    why="Holding stock costs space, watching and loss to theft beyond the spoilage the good's own "
        "data gives. None of that is modelled, so holding costs only the interest and spoilage.")


@dataclass(frozen=True)
class Producer:
    agent_id: AgentId
    owner: AgentId
    recipe_id: str
    tile: TileId
    capacity_runs: float                    # runs a year the plant and site allow
    yield_factor: float = 1.0               # set yearly by the engine: weather, depletion, site quality
    expected_prices: Mapping[GoodId, float] = field(default_factory=dict)   # outputs, adaptive
    years_of_loss: int = 0
    cash_target: float = 0.0                # cash it keeps; the rest is paid out as dividends
    expected_sales: float = 0.0             # runs' worth of output it expects to sell a year; 0 unknown
    last_runs: float = -1.0                 # runs it worked last year; below zero before its first year
    land_rent_per_run: float = 0.0          # rent on the land a run works, set yearly by the land market
    land_run_cap: float = -1.0              # runs the land it was granted allows; below zero for no limit
    workshops: int = 1                      # independent workshops it stands for: each newcomer to its recipe and tile joins it


@dataclass(frozen=True)
class Plan:
    runs: float
    labour_bids: Tuple[LabourBid, ...] = ()
    bids: Tuple[Bid, ...] = ()
    expected_margin_per_run: float = 0.0    # before the capital charge; what an idle producer weighs
    wanted_runs: float = 0.0                # runs it wanted before the land it was granted capped them
    wage_line: float = 0.0                  # cash the plan sets for the planned runs' labour


def expected_price(producer: Producer, good: GoodId, view: MarketView) -> Optional[float]:
    """The producer's own expectation, else last year's clearing price, else None."""
    if good in producer.expected_prices:
        return producer.expected_prices[good]
    return view.price(good, view.area_of(good, producer.tile))


def expected_output_prices(producer: Producer, recipe: Recipe, view: MarketView) -> Dict[GoodId, float]:
    prices = {}
    for good in recipe.outputs:
        price = expected_price(producer, good, view)
        if price is not None:
            prices[good] = price
    return prices


_names_of_recipe: Dict[int, tuple] = {}      # id of a recipe -> (recipe, its goods and its trades, sorted)


def _fallback_goods(recipe: Recipe) -> set:
    return {step.good for steps in recipe.tool_fallbacks.values() for step in steps if step.good}


def _priced_names(recipe: Recipe) -> tuple:
    """(goods, trades) a recipe's costs need prices for, sorted; worked out once per recipe."""
    kept = _names_of_recipe.get(id(recipe))
    if kept is None or kept[0] is not recipe:
        kept = _names_of_recipe[id(recipe)] = (
            recipe, tuple(sorted(set(recipe.inputs) | set(recipe.plant_goods) | _fallback_goods(recipe))),
            tuple(sorted(set(recipe.labour_hours) | set(recipe.plant_labour_hours))))
    return kept[1], kept[2]


def live_input_prices(producer: Producer, recipe: Recipe, view: MarketView) -> Dict[GoodId, float]:
    """Last year's prices of every good the run or its plant uses; goods never traded are absent."""
    return live_input_prices_at(producer.tile, recipe, view)


def live_input_prices_at(tile: TileId, recipe: Recipe, view: MarketView) -> Dict[GoodId, float]:
    """`live_input_prices` for a recipe worked on a tile, with no producer there yet."""
    goods = _priced_names(recipe)[0]
    present_prices_at = getattr(view, "present_prices_at", None)
    if present_prices_at is not None:
        return present_prices_at(goods, tile)
    prices = {}
    for good in goods:
        price = view.price(good, view.area_of(good, tile))
        if price is not None:
            prices[good] = price
    return prices


def paid_input_prices(producer: Producer, recipe: Recipe, view: MarketView,
                      live: Dict[GoodId, float]) -> Dict[GoodId, float]:
    """`live` with each input the run uses up raised to the price it cleared at last year in the producer's
    market, where that is higher than the remembered price: a thin trade moves the remembered price only
    slightly, and a buyer bidding from it is outbid every year. A view that does not report clearing prices
    leaves `live` as it is."""
    cleared_price = getattr(view, "cleared_price", None)
    if cleared_price is None:
        return live
    paid = dict(live)
    for good in recipe.inputs:
        cleared = cleared_price(good, view.area_of(good, producer.tile))
        if cleared is not None and cleared > paid.get(good, math.inf):
            paid[good] = cleared
    return paid


def expected_input_prices(producer: Producer, recipe: Recipe, view: MarketView,
                          live: Optional[Dict[GoodId, float]] = None) -> Dict[str, float]:
    """The prices a plan costs a run at: for a good the run uses up, the producer's own expectation
    (moved only part of the way to each year's price, so one year's spike does not swing its runs), else
    last year's price; plant goods and anything never expected keep last year's. `live` is
    `live_input_prices` when the caller has it already."""
    prices = live_input_prices(producer, recipe, view) if live is None else dict(live)
    return _with_expected(prices, recipe, producer.expected_prices)


def _with_expected(prices: Dict[GoodId, float], recipe: Recipe, expected: Mapping[GoodId, float]) -> Dict[GoodId, float]:
    """`prices` (changed in place) with each good the run uses up at its expected price where there is one."""
    for good in recipe.inputs:
        if good in prices and good in expected:
            prices[good] = expected[good]
    return prices


def live_wages(producer: Producer, recipe: Recipe, view: MarketView) -> Dict[str, float]:
    return live_wages_at(producer.tile, recipe, view)


def live_wages_at(tile: TileId, recipe: Recipe, view: MarketView) -> Dict[str, float]:
    """`live_wages` for a recipe worked on a tile, with no producer there yet."""
    trades = _priced_names(recipe)[1]
    present_prices_at = getattr(view, "present_prices_at", None)
    if present_prices_at is not None:
        return present_prices_at(trades, tile, True)
    wages = {}
    for trade in trades:
        wage = view.wage(trade, view.area_of(trade, tile))
        if wage is not None:
            wages[trade] = wage
    return wages


def next_expectations(producer: Producer, recipe: Recipe, view: MarketView,
                      live_inputs: Optional[Dict[GoodId, float]] = None,
                      wages: Optional[Dict[str, float]] = None) -> Dict[GoodId, float]:
    """Expected prices, for outputs and for the inputs a run uses up, moved toward the latest clearing
    prices. Output prices also go part of the way back toward what a run costs to make
    (REGRESSIVE_EXPECTATION_WEIGHT): a producer knows a price far above cost brings more output and one
    far below drives makers out. A good with no price keeps its old one. `live_inputs` and `wages` are
    `live_input_prices` and `live_wages` when the caller has them already."""
    updated = dict(producer.expected_prices)
    latest_prices = {}
    for good in recipe.outputs:
        latest = view.price(good, view.area_of(good, producer.tile))
        if latest is None:
            continue
        latest_prices[good] = latest
        previous = updated.get(good)
        updated[good] = latest if previous is None else (
            previous + EXPECTATION_ADJUSTMENT_SHARE * (latest - previous))
    if live_inputs is None:
        seen_inputs = {good: price for good, price in ((good, view.price(good, view.area_of(good, producer.tile)))
                                                       for good in recipe.inputs) if price is not None}
    else:
        seen_inputs = live_inputs       # the same prices, read already for every good the run or its plant uses
    paid_inputs = paid_input_prices(producer, recipe, view, seen_inputs)
    for good in recipe.inputs:
        latest = paid_inputs.get(good)
        if latest is not None and good not in recipe.outputs:
            previous = updated.get(good)
            updated[good] = latest if previous is None else (
                previous + EXPECTATION_ADJUSTMENT_SHARE * (latest - previous))
    break_even, input_share = _break_even_scale(producer, recipe, view, updated, live_inputs, wages)
    cost_covering = {good: updated[good] * break_even for good in latest_prices} if break_even is not None else {}
    if break_even is not None:
        for good in latest_prices:
            updated[good] += REGRESSIVE_EXPECTATION_WEIGHT * (updated[good] * break_even - updated[good])
    for good in ask_raise.sold_out_outputs(producer, recipe, view):
        if good in latest_prices:
            updated[good] = ask_raise.raised_within_band(updated[good], cost_covering.get(good), input_share=input_share)
    return updated


def _break_even_scale(producer, recipe, view, prices, live_inputs=None, wages=None) -> Tuple[Optional[float], float]:
    """(what the output prices would have to be multiplied by for a run to just repay its variable cost
    and its plant at the live rate, the share of that cost that is bought inputs); the scale is None when it
    cannot be worked out."""
    inputs = _with_expected(live_input_prices(producer, recipe, view) if live_inputs is None else dict(live_inputs),
                            recipe, prices)
    wages = live_wages(producer, recipe, view) if wages is None else wages
    revenue = unit_cost.revenue_per_run(recipe, prices) * producer.yield_factor
    rate = view.interest_rate(view.currency_of(view.area_of(min(recipe.outputs), producer.tile)))
    cost = unit_cost.variable_cost_per_run(recipe, inputs, wages, producer.land_rent_per_run) + unit_cost.capital_charge_per_run(
        recipe, inputs, wages, rate)
    if not (revenue > 0.0 and math.isfinite(cost) and cost > 0.0):
        return None, 0.0
    return cost / revenue, unit_cost.input_cost_per_run(recipe, inputs) / cost


def plan(producer: Producer, recipe: Recipe, view: MarketView, cash: float) -> Plan:
    """Runs this year and the orders that carry them out. Idle (zero runs, no orders) when a run's
    expected revenue, after the yield, does not cover its variable cost at expected input prices and
    live wages."""
    outputs = expected_output_prices(producer, recipe, view)
    market_inputs = paid_input_prices(producer, recipe, view, live_input_prices(producer, recipe, view))
    inputs = expected_input_prices(producer, recipe, view, market_inputs)
    wages = live_wages(producer, recipe, view)
    revenue = unit_cost.revenue_per_run(recipe, outputs) * producer.yield_factor
    input_cost = unit_cost.input_cost_per_run(recipe, inputs)
    labour_cost = unit_cost.labour_cost_per_run(recipe, wages)
    rent = producer.land_rent_per_run
    variable = input_cost + labour_cost + rent
    margin = revenue - variable
    if producer.capacity_runs <= 0.0 or revenue <= 0.0 or not math.isfinite(variable):
        return Plan(0.0, expected_margin_per_run=margin)
    # cash pays what the market asks now (as the cash target is struck); the lagging expectation only chooses runs
    paying_prices = {**inputs, **market_inputs}
    held_value = sum(min(view.stock(producer.agent_id, good, producer.tile), quantity * producer.capacity_runs)
                     * paying_prices[good] for good, quantity in recipe.inputs.items())
    paid_now = unit_cost.input_cost_per_run(recipe, paying_prices) + labour_cost     # rent falls due at the year's end, out of the sales
    affordable = (max(cash, 0.0) + held_value) / paid_now if paid_now > 0.0 else producer.capacity_runs
    # working off stock is a choice and moves at the year's pace; cash and held inputs bind after it
    chosen = min(producer.capacity_runs * share_working(revenue, variable),
                 runs_for_stock(producer, recipe, view, variable, outputs))
    runs = max(0.0, min(within_a_years_change(producer, chosen), affordable))
    wanted = runs
    if producer.land_run_cap >= 0.0:
        runs = min(runs, producer.land_run_cap)
    ratio = working_cost_ratio(revenue, variable)
    if runs <= 0.0 or ratio <= 0.0:
        return Plan(0.0, expected_margin_per_run=margin, wanted_runs=wanted)
    # the workplaces that work are the cheaper ones: what an hour or an input is worth is judged at their cost
    labour_bids = _labour_bids(producer, recipe, view, runs, revenue / ratio, input_cost + rent, wages)
    # an input is bid up to the price at which the run breaks even at the input prices seen now, not at the
    # lagging expectation the run is planned on, or a scarce input's price ratchets up on its own bid
    live_variable = unit_cost.input_cost_per_run(recipe, {**inputs, **market_inputs}) + labour_cost + rent
    bids = _input_bids(producer, recipe, view, runs, market_inputs, max(cash, 0.0) - runs * labour_cost,
                       revenue / ratio - live_variable, live_variable, wages)
    return Plan(runs, tuple(labour_bids), tuple(bids), margin, wanted, runs * labour_cost)


def within_a_years_change(producer: Producer, runs: float) -> float:
    """Runs no further from last year's than hiring, training and laying off allow in a year
    (OUTPUT_CHANGE_SHARE_PER_YEAR of capacity); a producer in its first year starts where it likes."""
    if producer.last_runs < 0.0:
        return runs
    step = OUTPUT_CHANGE_SHARE_PER_YEAR * producer.capacity_runs
    return max(producer.last_runs - step, min(producer.last_runs + step, runs))


def next_years_runs_ceiling(producer: Producer) -> float:
    """The most runs the producer could plan next year: its working scale plus a year's change."""
    if producer.last_runs < 0.0:
        return producer.capacity_runs
    scale = max(producer.last_runs, producer.expected_sales)
    return min(producer.capacity_runs, scale + OUTPUT_CHANGE_SHARE_PER_YEAR * producer.capacity_runs)


def share_that_pays(producer: Producer, recipe: Recipe, view: MarketView,
                    outputs: Optional[Mapping[GoodId, float]] = None) -> float:
    """Share of the plant a run pays at the prices it plans with (the share `plan` would work at no cash
    limit): none when a run's expected revenue does not cover its variable cost or an input cannot be
    priced. `outputs` is `expected_output_prices` when the caller has it already."""
    if outputs is None:
        outputs = expected_output_prices(producer, recipe, view)
    variable = (unit_cost.variable_cost_per_run(recipe, expected_input_prices(producer, recipe, view),
                                                live_wages(producer, recipe, view), producer.land_rent_per_run))
    if not math.isfinite(variable):
        return 0.0
    return share_working(unit_cost.revenue_per_run(recipe, outputs) * producer.yield_factor, variable)


def shortfall_at_working_scale(producer: Producer, recipe: Recipe, view: MarketView, cash_shortfall: float,
                               outputs: Optional[Mapping[GoodId, float]] = None) -> float:
    """The cash it lacks for the runs it could plan next year and that would pay. The cash target covers
    the whole plant; a producer working a small part of it, or none because a run does not pay, is not
    pressed to sell stock at any price for want of working capital it has no use for. `outputs` is
    `expected_output_prices` when the caller has it already."""
    if producer.capacity_runs <= 0.0:
        return cash_shortfall
    if not cash_shortfall > 0.0:
        return 0.0          # nothing is lacking, so there is no shortfall to shrink
    scale = next_years_runs_ceiling(producer) * share_that_pays(producer, recipe, view, outputs)
    unused_share = 1.0 - scale / producer.capacity_runs
    return max(0.0, cash_shortfall - unused_share * producer.cash_target)


def share_working(revenue_per_run: float, variable_cost_per_run: float) -> float:
    """Share of the producer's workplaces whose own cost the expected revenue covers: the workplaces'
    costs spread log-normally (COST_SPREAD_WITHIN_PRODUCER) with the producer's cost as their mean."""
    if variable_cost_per_run <= 0.0:
        return 1.0
    if revenue_per_run <= 0.0:
        return 0.0
    return _normal_below(_standard_score(revenue_per_run, variable_cost_per_run))


def _standard_score(revenue_per_run: float, mean_cost_per_run: float) -> float:
    """How many spreads the revenue sits above the median workplace's cost (the mean is the average)."""
    spread = COST_SPREAD_WITHIN_PRODUCER
    return (math.log(revenue_per_run / mean_cost_per_run) + spread * spread / 2.0) / spread


def _normal_below(score: float) -> float:
    return 0.5 * (1.0 + math.erf(score / math.sqrt(2.0)))


def working_cost_ratio(revenue_per_run: float, variable_cost_per_run: float) -> float:
    """The average cost of the workplaces that work, against the producer's average cost: below one,
    since only those whose cost the revenue covers work."""
    if variable_cost_per_run <= 0.0 or revenue_per_run <= 0.0:
        return 1.0
    score = _standard_score(revenue_per_run, variable_cost_per_run)
    working = _normal_below(score)
    if working <= 0.0:
        return 1.0
    return _normal_below(score - COST_SPREAD_WITHIN_PRODUCER) / working


_main_output_of_recipe: Dict[int, tuple] = {}      # id of a recipe -> (recipe, its main output)


def main_output(recipe: Recipe) -> GoodId:
    """The output a run makes most of (the first by name among ties); worked out once per recipe."""
    kept = _main_output_of_recipe.get(id(recipe))
    if kept is None or kept[0] is not recipe:
        kept = _main_output_of_recipe[id(recipe)] = (
            recipe, max(sorted(recipe.outputs), key=lambda good: recipe.outputs[good]))
    return kept[1]


def runs_for_stock(producer: Producer, recipe: Recipe, view: MarketView, run_cost: Optional[float] = None,
                   output_prices: Optional[Mapping[GoodId, float]] = None) -> float:
    """Runs a producer holding more than its target stock of an output limits itself to: what it expects to
    sell less a share of the excess (one over STOCK_CLEARING_YEARS), so unsold output is worked off over those years. Below its target, the price decides alone (a cap tied
    to past sales would follow output down, since nothing sells that is not made). Unlimited while it has no
    record of sales. With the run's cost and the outputs' prices, outputs that are piling up do not count while
    what a run makes of the others, at those prices, covers the cost: a joint recipe runs for the output that pays."""
    if producer.expected_sales <= 0.0:
        return math.inf
    sales = producer.expected_sales
    target = inventory.target_stock(sales)
    excess = {good: view.stock(producer.agent_id, good, producer.tile) / made - target
              for good, made in recipe.outputs.items() if made > 0.0}
    piling = [good for good, over in excess.items() if over > 0.0]
    if not piling:
        return math.inf
    if run_cost is not None and output_prices is not None:
        sells = math.fsum(made * output_prices.get(good, 0.0) for good, made in recipe.outputs.items()
                          if good not in piling) * producer.yield_factor
        if sells > 0.0 and sells >= run_cost:      # nothing else sold covers nothing: a costless run is not paid for by it
            return math.inf
    # excess is drawn down over STOCK_CLEARING_YEARS: output falls to zero only for stock that cannot clear in them
    return max(0.0, sales - max(excess[good] for good in piling) / STOCK_CLEARING_YEARS)


def _labour_bids(producer, recipe, view, runs, revenue, input_cost, wages) -> List[LabourBid]:
    """Each trade's hours, at most what an hour is worth: the run's revenue less inputs and the other
    trades' wages, shared over that trade's hours."""
    bids = []
    for trade in sorted(recipe.labour_hours):
        hours_per_run = recipe.labour_hours[trade]
        others = sum(hours * wages[other] for other, hours in recipe.labour_hours.items() if other != trade)
        worth = max(0.0, (revenue - input_cost - others) / hours_per_run)
        bids.append(LabourBid(producer.agent_id, trade, view.area_of(trade, producer.tile),
                              runs * hours_per_run, worth))
    return bids


def input_ceiling(price: float, margin_per_run: float, variable_cost_per_run: float,
                  value_in_use: Optional[float] = None) -> float:
    """The most a buyer bids for an input: its price plus the share of the run's margin the input accounts for
    (its share of the run's variable cost), and never more than the input is worth against its cheapest
    substitute when it has one. Short supply is rationed by bid inside this bound, not by a bound that moves
    with the price bid."""
    worth = price * (1.0 + max(0.0, margin_per_run) / variable_cost_per_run) if variable_cost_per_run > 0.0 else price
    return worth if value_in_use is None else min(worth, value_in_use)


def _input_bids(producer, recipe, view, runs, prices, budget_for_inputs, margin_per_run, variable_cost_per_run=0.0,
                wages=None) -> List[Bid]:
    """Inputs for the planned runs, net of what is held: a floor, not price-sensitive. The budget is
    the cash left after wages, split by cost share, so the bids never add up to more than the cash.
    No input is bid for above `input_ceiling`: the run's margin shared by the input's cost share, and the
    input's value against its cheapest substitute (the tool basket's later tools, or working by hand)."""
    needs = {}
    for good, per_run in sorted(recipe.inputs.items()):
        short = runs * per_run - view.stock(producer.agent_id, good, producer.tile)
        if short > 0.0:
            needs[good] = short
    for steps in recipe.tool_fallbacks.values():     # the tools drawn when the first is short are held against it
        for step in steps:
            short = runs * step.units_per_run - view.stock(producer.agent_id, step.good, producer.tile) if step.good else 0.0
            if short > 0.0 and prices.get(step.good, 0.0) > 0.0:
                needs[step.good] = needs.get(step.good, 0.0) + short
    total_cost = sum(quantity * prices[good] for good, quantity in needs.items())
    bids = []
    for good, quantity in needs.items():
        share = quantity * prices[good] / total_cost if total_cost > 0.0 else 0.0
        worth = input_ceiling(prices[good], margin_per_run, variable_cost_per_run,
                              tool_fallback.value_in_use(recipe, good, prices, wages or {}))
        bids.append(Bid(producer.agent_id, good, view.area_of(good, producer.tile), producer.tile,
                        quantity, 0.0, prices[good], 0.0, max(0.0, budget_for_inputs) * share,
                        maximum_price=worth))
    return bids


def produce(producer: Producer, recipe: Recipe, inputs_held: Mapping[GoodId, float],
            hours_hired: Mapping[str, float], runs_planned: Optional[float] = None
            ) -> Tuple[float, List[GoodsMove]]:
    """Runs achieved, with the goods moves that book them. The scarcest of inputs, hours, the plan and
    the capacity sets how many runs go ahead (Leontief); the yield factor scales what comes out, not
    what goes in. Tools are not an input that stops a run: a run short of its tool draws the recipe's next
    tool (`tool_fallbacks`), then works by hand, and the extra hours that takes can lower the runs the hours
    hired allow."""
    limit = producer.capacity_runs if runs_planned is None else min(runs_planned, producer.capacity_runs)
    for good, per_run in recipe.hard_inputs.items():
        limit = min(limit, inputs_held.get(good, 0.0) / per_run)
    for trade, per_run in recipe.labour_hours.items():
        limit = min(limit, hours_hired.get(trade, 0.0) / per_run)
    limit = max(0.0, limit)
    moves = []
    if limit <= 0.0:
        return 0.0, moves
    draws, extra_hours = tool_fallback.draws(recipe, inputs_held, limit)
    for trade, extra in extra_hours.items():
        stretched = recipe.labour_hours[trade] * limit + extra
        if stretched > hours_hired.get(trade, 0.0):
            limit *= max(0.0, hours_hired.get(trade, 0.0) / stretched)
    if limit <= 0.0:
        return 0.0, moves
    if extra_hours:
        draws, extra_hours = tool_fallback.draws(recipe, inputs_held, limit)
    for good, per_run in sorted(recipe.hard_inputs.items()):
        used = min(limit * per_run, inputs_held.get(good, 0.0))   # never more than held, to the last bit
        moves.append(GoodsMove(producer.agent_id, EDGE_CONSUMPTION, good, producer.tile, used, "input"))
    for good, used in sorted(draws.items()):
        if used > 0.0:
            moves.append(GoodsMove(producer.agent_id, EDGE_CONSUMPTION, good, producer.tile, used, "input"))
    achieved = limit * producer.yield_factor
    for good, per_run in sorted(recipe.outputs.items()):
        if achieved * per_run > 0.0:
            moves.append(GoodsMove(EDGE_PRODUCTION, producer.agent_id, good, producer.tile,
                                   achieved * per_run, "output"))
    return achieved, moves


def offers(producer: Producer, recipe: Recipe, view: MarketView, stock_by_good: Mapping[GoodId, float],
           cash_shortfall: float, interest_rate: float, specs: Mapping[GoodId, GoodSpec],
           keep_back: Optional[Mapping[GoodId, float]] = None) -> List[Offer]:
    """Held output on each output's own market. The reservation is what carrying a unit to next year
    would net at the expected price, lowered when cash is short; what was spent making it does not
    enter. A perishable's reservation falls to or below zero, so it sells at any price. `keep_back`
    holds stock the producer needs as input for its own planned runs."""
    keep_back = keep_back or {}
    expected = expected_output_prices(producer, recipe, view)
    rows = []
    for good in sorted(recipe.outputs):
        quantity = stock_by_good.get(good, 0.0) - keep_back.get(good, 0.0)
        if quantity <= 0.0:
            continue
        spoilage = specs[good].spoilage_per_year if good in specs else 0.0
        reservation = inventory.holding_reservation(expected.get(good, 0.0), interest_rate, spoilage,
                                                    STORAGE_COST_PER_UNIT)
        rows.append((good, quantity, reservation))
    stock_value = sum(quantity * max(reservation, 0.0) for _good, quantity, reservation in rows)
    cash_shortfall = shortfall_at_working_scale(producer, recipe, view, cash_shortfall, expected)
    return [Offer(producer.agent_id, good, view.area_of(good, producer.tile), producer.tile, quantity,
                  inventory.distressed_reservation(reservation, cash_shortfall, stock_value))
            for good, quantity, reservation in rows]


def with_capacity(producer: Producer, capacity_runs: float) -> Producer:
    return replaced(producer, capacity_runs=max(0.0, capacity_runs))
