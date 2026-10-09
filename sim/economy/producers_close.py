"""A producer's year end and the entry of new ones: dividends, expansion, wear and exit.

`close_year(producer, recipe, revenue, costs, view)` -> `YearClose`
    pays the owner the cash above the producer's target, applies wear to the plant, counts a loss
    year when revenue did not cover the costs paid plus the plant's charge at the live rate, exits
    after enough of them, and asks for a loan to rebuild and grow when new plant would earn more than
    the live rate. A funded loan becomes capacity through `producers.with_capacity`.
`entrants(recipes, view, sites, occupied)` -> new `Producer`s where the expected return beats the live
    rate, best first, at most a declared number a year. Owners and sites come from the caller.
"""
import math
from dataclasses import dataclass, replace
from typing import Collection, List, Mapping, Optional, Sequence, Tuple

from sim.constants import declare

from . import unit_cost
from .producers import (OUTPUT_CHANGE_SHARE_PER_YEAR, Producer, expected_output_prices, live_input_prices,
                        live_wages, next_expectations, share_working)
from .protocols import MarketView
from .types import AgentId, LoanRequest, Recipe, TileId, Transfer

LOSS_YEARS_BEFORE_EXIT = declare(
    "LOSS_YEARS_BEFORE_EXIT", 3, kind="temporary_heuristic", unit="consecutive years",
    source=None, confidence="D",
    why="An owner keeps a losing producer going for a while on hope, reserves and the cost of "
        "closing. How long follows the owner's wealth and credit, which are not yet tied to the "
        "decision; one count for every producer.")
IDLE_CAPACITY_DECAY_SHARE = declare(
    "IDLE_CAPACITY_DECAY_SHARE", 0.25, kind="temporary_heuristic",
    unit="share of the gap between capacity and runs worked that is given up in a year", source=None,
    confidence="D",
    why="Capacity with no plant is hands and tools kept for work: unused while its runs would not pay, "
        "the hands leave and the workings fall in. How fast follows hiring contracts and the cost of reopening a working, "
        "which are not modelled; one share for every plantless recipe.")
WORKING_CAPITAL_YEARS_OF_VARIABLE_COST = declare(
    "WORKING_CAPITAL_YEARS_OF_VARIABLE_COST", 1.0, kind="temporary_heuristic",
    unit="years of full-capacity variable cost", source=None, confidence="D",
    why="Inputs and wages are paid before the year's sales in a model with one clearing a year, so "
        "a producer keeps a year of them. The true float follows the production cycle and the "
        "credit on offer, which are not modelled.")
CLOSED_CAPACITY_SHARE = declare(
    "CLOSED_CAPACITY_SHARE", 0.01, kind="temporary_heuristic",
    unit="share of a producer's workplaces whose cost the expected revenue covers", source=None, confidence="D",
    why="A producer leaves at once only when next to no workplace in its market could cover its variable cost "
        "at the prices it expects; while some could, the rest close at the pace workplaces change and the "
        "market keeps the makers it has. Below this share the sliver stands for no market at all.")
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
               worked_runs: Optional[float] = None) -> YearClose:
    """`worked_runs` is what the producer ran this year (all its capacity when not given). Idle plant is
    sunk, so the year's capital charge falls only on the capacity worked."""
    first_output = sorted(recipe.outputs)[0]
    currency = view.currency_of(view.area_of(first_output, producer.tile))
    rate = view.interest_rate(currency)
    cash = max(0.0, view.cash(producer.agent_id, currency))
    inputs = live_input_prices(producer, recipe, view)
    wages = live_wages(producer, recipe, view)
    expectations = next_expectations(producer, recipe, view)
    worked = producer.capacity_runs if worked_runs is None else min(max(0.0, worked_runs), producer.capacity_runs)
    charge = unit_cost.capital_charge_per_run(recipe, inputs, wages, rate) * worked
    loss = worked <= 0.0 or revenue < costs + (charge if math.isfinite(charge) else 0.0)
    losses = producer.years_of_loss + 1 if loss else 0
    has_plant = recipe.plant_life_years > 0.0
    revenue_per_run, cost_per_run = _expected_run(producer, recipe, view, expectations, inputs, wages)
    margin = revenue_per_run - cost_per_run
    paying = share_working(revenue_per_run, cost_per_run) if math.isfinite(margin) else 0.0
    shedding = losses >= LOSS_YEARS_BEFORE_EXIT and margin <= 0.0
    if shedding and paying < CLOSED_CAPACITY_SHARE:
        payout = _dividend(producer, currency, cash)
        gone = replace(producer, capacity_runs=0.0, years_of_loss=losses, expected_prices=expectations,
                       cash_target=0.0)
        return YearClose(gone, payout, exited=True)
    if has_plant:
        wear = producer.capacity_runs / recipe.plant_life_years     # sunk plant is kept while it covers variable cost
        capacity = producer.capacity_runs - wear
    else:
        wear = 0.0
        # hands are let go when their work would not pay; a workshop waiting on inputs or buyers keeps them
        idle = producer.capacity_runs - worked if margin <= 0.0 else 0.0
        capacity = producer.capacity_runs - IDLE_CAPACITY_DECAY_SHARE * idle
    if shedding:
        # one producer stands for every workplace in its market: those whose cost the price does not cover
        # close, no faster than workplaces open (OUTPUT_CHANGE_SHARE_PER_YEAR), and those that pay stay
        capacity = min(capacity, max(paying * producer.capacity_runs,
                                     (1.0 - OUTPUT_CHANGE_SHARE_PER_YEAR) * producer.capacity_runs))
    target = working_capital_target(recipe, capacity, inputs, wages)
    request, rebuilt = _expansion(producer, recipe, view, currency, rate, wear, inputs, wages)
    survivor = replace(producer, capacity_runs=capacity, years_of_loss=losses,
                       expected_prices=expectations, cash_target=target)
    surplus = max(0.0, cash - target)
    return YearClose(survivor, _dividend(producer, currency, surplus), request, rebuilt)


def _expected_run(producer, recipe, view, expectations, inputs, wages) -> Tuple[float, float]:
    """(expected revenue, variable cost) of one run at expected prices; plant already built is sunk and left
    out. A cost or price that cannot be known counts as no margin: (0, infinity)."""
    prices = {good: expectations.get(good, view.price(good, view.area_of(good, producer.tile)))
              for good in recipe.outputs}
    if any(price is None for price in prices.values()):
        return 0.0, math.inf
    cost = unit_cost.variable_cost_per_run(recipe, inputs, wages, producer.land_rent_per_run)
    if not math.isfinite(cost):
        return 0.0, math.inf
    return unit_cost.revenue_per_run(recipe, prices) * producer.yield_factor, cost


def _dividend(producer: Producer, currency: str, amount: float) -> Tuple[Transfer, ...]:
    if amount <= 0.0:
        return ()
    return (Transfer(producer.agent_id, producer.owner, currency, amount, "dividend"),)


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
