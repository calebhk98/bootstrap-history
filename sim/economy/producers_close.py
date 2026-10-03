"""A producer's year end and the entry of new ones: dividends, expansion, wear and exit.

`close_year(producer, recipe, revenue, costs, view)` -> `YearClose`
    pays the owner the cash above the producer's target, applies wear to the plant, counts a loss
    year when revenue did not cover the costs paid plus the plant's charge at the live rate, exits
    after enough of them, and asks for a loan to rebuild and grow when new plant would earn more than
    the live rate. A funded loan becomes capacity through `producers.with_capacity`; a maker with no
    plant and no land grows its capacity directly while its full runs pay.
`entrants(recipes, view, sites, occupied)` -> new `Producer`s where the expected return beats the live
    rate, best first, at most a declared number a year. Owners and sites come from the caller.
"""
import math
from dataclasses import dataclass, replace
from typing import Collection, List, Mapping, Optional, Sequence, Tuple

from sim.constants import declare

from . import unit_cost
from .producers import (Producer, expected_output_prices, live_input_prices, live_wages,
                        next_expectations, runs_for_stock)
from .protocols import MarketView
from .types import AgentId, LoanRequest, Recipe, TileId, Transfer

LOSS_YEARS_BEFORE_EXIT = declare(
    "LOSS_YEARS_BEFORE_EXIT", 3, kind="temporary_heuristic", unit="consecutive years",
    source=None, confidence="D",
    why="An owner keeps a losing producer going for a while on hope, reserves and the cost of "
        "closing. How long follows the owner's wealth and credit, which are not yet tied to the "
        "decision; one count for every producer.")
WORKING_CAPITAL_YEARS_OF_VARIABLE_COST = declare(
    "WORKING_CAPITAL_YEARS_OF_VARIABLE_COST", 1.0, kind="temporary_heuristic",
    unit="years of full-capacity variable cost", source=None, confidence="D",
    why="Inputs and wages are paid before the year's sales in a model with one clearing a year, so "
        "a producer keeps a year of them. The true float follows the production cycle and the "
        "credit on offer, which are not modelled.")
EXPANSION_SHARE_PER_YEAR = declare(
    "EXPANSION_SHARE_PER_YEAR", 0.1, kind="temporary_heuristic",
    unit="share of current capacity added in a year", source=None, confidence="D",
    why="Plant takes time to build and a lender to find; how fast a profitable producer grows is "
        "bounded by both, which are not yet modelled. A bound keeps growth gradual.")
@dataclass(frozen=True)
class YearClose:
    producer: Producer
    transfers: Tuple[Transfer, ...] = ()
    loan_request: Optional[LoanRequest] = None
    expansion_runs: float = 0.0     # capacity the loan, if funded, builds: wear replaced plus growth
    exited: bool = False


def working_capital_target(recipe: Recipe, capacity_runs: float, input_prices, wages) -> float:
    cost = unit_cost.variable_cost_per_run(recipe, input_prices, wages)
    if not math.isfinite(cost):
        return 0.0
    return cost * capacity_runs * WORKING_CAPITAL_YEARS_OF_VARIABLE_COST


def close_year(producer: Producer, recipe: Recipe, revenue: float, costs: float, view: MarketView,
               uses_land: bool = False) -> YearClose:
    first_output = sorted(recipe.outputs)[0]
    currency = view.currency_of(view.area_of(first_output, producer.tile))
    rate = view.interest_rate(currency)
    cash = max(0.0, view.cash(producer.agent_id, currency))
    inputs = live_input_prices(producer, recipe, view)
    wages = live_wages(producer, recipe, view)
    expectations = next_expectations(producer, recipe, view)
    charge = unit_cost.capital_charge_per_run(recipe, inputs, wages, rate) * producer.capacity_runs
    loss = revenue < costs + (charge if math.isfinite(charge) else 0.0)
    losses = producer.years_of_loss + 1 if loss else 0
    if losses >= LOSS_YEARS_BEFORE_EXIT:
        payout = _dividend(producer, currency, cash)
        gone = replace(producer, capacity_runs=0.0, years_of_loss=losses, expected_prices=expectations,
                       cash_target=0.0)
        return YearClose(gone, payout, exited=True)
    wear = producer.capacity_runs / recipe.plant_life_years if recipe.plant_life_years > 0.0 else 0.0
    capacity = producer.capacity_runs - wear
    target = working_capital_target(recipe, capacity, inputs, wages)
    request, rebuilt = _expansion(producer, recipe, view, currency, rate, wear, inputs, wages)
    if _grows_without_plant(producer, recipe, view, rate, inputs, wages, uses_land):
        capacity *= 1.0 + EXPANSION_SHARE_PER_YEAR
    survivor = replace(producer, capacity_runs=capacity, years_of_loss=losses,
                       expected_prices=expectations, cash_target=target)
    surplus = max(0.0, cash - target)
    return YearClose(survivor, _dividend(producer, currency, surplus), request, rebuilt)


def plant_bid_ceiling(price: float, yearly_return: float) -> float:
    """The most a producer pays for a unit of plant good: last price plus what building a year later
    would forgo, a year's return on it. Dearer than that, it waits for makers to catch up."""
    return price * (1.0 + max(0.0, yearly_return))


def _dividend(producer: Producer, currency: str, amount: float) -> Tuple[Transfer, ...]:
    if amount <= 0.0:
        return ()
    return (Transfer(producer.agent_id, producer.owner, currency, amount, "dividend"),)


def _grows_without_plant(producer, recipe, view, rate, inputs, wages, uses_land) -> bool:
    """A maker with no plant to build and no land to find takes on more hands and room while it sells
    what it makes (it holds no more than its target stock) and its runs pay more than the live rate;
    one on land waits for land to carry a rent (Complaint 393), since free land would let it grow
    without bound."""
    if uses_land or recipe.plant_goods or recipe.plant_labour_hours or producer.capacity_runs <= 0.0:
        return False
    if math.isfinite(runs_for_stock(producer, recipe, view)):
        return False
    return unit_cost.return_on_capital(recipe, expected_output_prices(producer, recipe, view) or {},
                                       inputs, wages) > rate


def _expansion(producer, recipe, view, currency, rate, wear, inputs, wages):
    """A loan to grow, when a run of new capacity would earn more than the live rate. Plant that wore
    out is rebuilt from the producer's own cash (the economy's year does it). Only a recipe with
    plant needs one; without plant the site and the owner bound it."""
    value = unit_cost.plant_value_per_run(recipe, inputs, wages)
    if recipe.plant_life_years <= 0.0 or value <= 0.0 or not math.isfinite(value):
        return None, 0.0
    yearly_return = unit_cost.return_on_capital(
        recipe, expected_output_prices(producer, recipe, view) or {}, inputs, wages)
    if yearly_return <= rate:
        return None, 0.0
    runs = EXPANSION_SHARE_PER_YEAR * producer.capacity_runs
    amount = runs * value
    return LoanRequest(producer.agent_id, currency, amount, yearly_return, recipe.plant_life_years,
                       amount, "expand"), runs
