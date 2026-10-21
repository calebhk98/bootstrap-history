"""A producer's year end and the entry of new ones: dividends, expansion, wear and exit.

`close_year(producer, recipe, revenue, costs, view)` -> `YearClose`
    pays the owner the cash above the producer's target, applies wear to the plant, counts a loss
    year when revenue did not cover the costs paid plus the plant's charge at the live rate, sheds
    workplaces whose expected sales do not cover running cost (all of them, so it exits, when none would), and asks for a loan to rebuild and grow when new plant would earn more than
    the live rate. A funded loan becomes capacity through `producers.with_capacity`.
`entrants(recipes, view, sites, occupied)` -> new `Producer`s where the expected return beats the live
    rate, best first, at most a declared number a year. Owners and sites come from the caller.
"""
import math
from dataclasses import dataclass
from typing import Callable, Collection, List, Mapping, Optional, Sequence, Tuple

from sim.constants import declare

from . import credit, idle_capacity, inventory, unit_cost
from .producers import (OUTPUT_CHANGE_SHARE_PER_YEAR, Producer, expected_output_prices, live_input_prices,
                        live_wages, next_expectations, share_working, within_a_years_change)
from .protocols import MarketView
from .types import AgentId, GoodId, LoanRequest, Recipe, TileId, Transfer
from .replaced import replaced

LOSS_YEARS_BEFORE_EXIT = declare(
    "LOSS_YEARS_BEFORE_EXIT", 3, kind="temporary_heuristic", unit="consecutive years",
    source=None, confidence="D",
    why="Entry (entry_margin.py) waits this many years of a standing margin before newcomers come. A producer's own "
        "exit no longer waits on it: plant is shed when expected sales do not cover running cost. How long newcomers "
        "wait follows their credit and the time to build, which are not yet tied to the decision.")
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
WORKING_CAPITAL_PURPOSE = "working capital"     # a loan for next year's running costs, never for plant


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
               worked_runs: Optional[float] = None,
               price_share_after: Optional[Callable[[GoodId, float], float]] = None,
               ground_goods: Collection[GoodId] = (), service_lives: Optional[Mapping[GoodId, float]] = None) -> YearClose:
    """`worked_runs` is what the producer ran this year (all its capacity when not given). Idle plant is
    sunk, so the year's capital charge falls only on the capacity worked. `price_share_after(good, added)` is
    the share of a good's price that remains when the producer adds that much output a year (expansion_price.py);
    without it the producer expects the price it sees. `service_lives` maps a good to the years it lasts: idle
    capacity with tools wears at theirs (idle_capacity.py)."""
    first_output = min(recipe.outputs)
    currency = view.currency_of(view.area_of(first_output, producer.tile))
    rate = view.interest_rate(currency)
    cash = max(0.0, view.cash(producer.agent_id, currency))
    inputs = live_input_prices(producer, recipe, view)
    wages = live_wages(producer, recipe, view)
    expectations = next_expectations(producer, recipe, view, inputs, wages)
    worked = producer.capacity_runs if worked_runs is None else min(max(0.0, worked_runs), producer.capacity_runs)
    charge = unit_cost.capital_charge_per_run(recipe, inputs, wages, rate) * worked
    loss = worked <= 0.0 or revenue < costs + (charge if math.isfinite(charge) else 0.0)
    losses = producer.years_of_loss + 1 if loss else 0
    has_plant = recipe.plant_life_years > 0.0
    revenue_per_run, cost_per_run = _expected_run(producer, recipe, view, expectations, inputs, wages, ground_goods)
    margin = revenue_per_run - cost_per_run
    paying = share_working(revenue_per_run, cost_per_run) if math.isfinite(margin) else 0.0
    shedding = margin <= 0.0      # expected sales do not cover running cost, whatever the years behind
    if shedding and paying < CLOSED_CAPACITY_SHARE:
        payout = _dividend(producer, currency, cash)
        gone = replaced(producer, capacity_runs=0.0, years_of_loss=losses, expected_prices=expectations,
                       cash_target=0.0)
        return YearClose(gone, payout, exited=True)
    if has_plant:
        wear = producer.capacity_runs / recipe.plant_life_years     # sunk plant is kept while it covers variable cost
        capacity = producer.capacity_runs - wear
    else:
        wear = 0.0
        # idle tools wear when the work would not pay; a workshop waiting on inputs or buyers keeps them
        idle = producer.capacity_runs - worked if margin <= 0.0 else 0.0
        capacity = producer.capacity_runs - idle_capacity.wear_share_per_year(recipe, service_lives or {}) * idle
    if shedding:
        # one producer stands for every workplace in its market: those whose cost the price does not cover
        # close, no faster than workplaces open (OUTPUT_CHANGE_SHARE_PER_YEAR), and those that pay stay. Not so many
        # close that the ones that pay (the share `paying`) would make less than it expects to sell: short supply
        # would lift the price until more of them paid, so workplaces its sales still need are not shed
        shed = min(capacity, max(paying * producer.capacity_runs,
                                 (1.0 - OUTPUT_CHANGE_SHARE_PER_YEAR) * producer.capacity_runs))
        needed = producer.expected_sales / paying if paying > 0.0 else producer.capacity_runs
        capacity = max(shed, min(capacity, needed))
    target = working_capital_target(recipe, capacity, inputs, wages)
    request, rebuilt = _expansion(producer, recipe, view, currency, rate, capacity, worked, inputs, wages,
                                  price_share_after)
    if request is None:
        request = _working_capital(producer, recipe, currency, worked, capacity, min(cash, target), paying,
                                   revenue_per_run, inputs, wages)
    survivor = replaced(producer, capacity_runs=capacity, years_of_loss=losses,
                       expected_prices=expectations, cash_target=target)
    surplus = max(0.0, cash - target)
    return YearClose(survivor, _dividend(producer, currency, surplus), request, rebuilt)


def _expected_run(producer, recipe, view, expectations, inputs, wages, ground_goods=()) -> Tuple[float, float]:
    """(expected revenue, variable cost) of one run at expected prices; plant already built is sunk and left
    out. A cost or price that cannot be known counts as no margin: (0, infinity)."""
    prices = {good: expectations[good] if good in expectations else view.price(good, view.area_of(good, producer.tile))
              for good in recipe.outputs}
    if any(price is None for price in prices.values()):
        return 0.0, math.inf
    prices = _behind_the_stock(producer, recipe, view, prices, ground_goods)
    cost = unit_cost.variable_cost_per_run(recipe, inputs, wages, producer.land_rent_per_run)
    if not math.isfinite(cost):
        return 0.0, math.inf
    return unit_cost.revenue_per_run(recipe, prices) * producer.yield_factor, cost


def _behind_the_stock(producer, recipe, view, prices, ground_goods):
    """A run's output joins the queue behind the stock the producer holds beyond its own runs' inputs, so it is
    worth what the last unit of that queue fetches (inventory.queued_holding_value): a producer holding years of
    unsold output does not count on the market's price, which a market with no trade leaves standing. Ground does
    not queue (every hectare yields its rent while held): its price stands."""
    if producer.expected_sales <= 0.0:
        return prices
    rate = view.interest_rate(view.currency_of(view.area_of(min(recipe.outputs), producer.tile)))
    return {good: inventory.queued_holding_value(
        price, max(0.0, view.stock(producer.agent_id, good, producer.tile) - recipe.inputs.get(good, 0.0) * producer.capacity_runs),
        producer.expected_sales * recipe.outputs[good], rate, 0.0) if good not in ground_goods else price
        for good, price in prices.items()}


def _working_capital(producer, recipe, currency, worked, capacity, cash_kept, paying, revenue_per_run, inputs, wages):
    """A one-year loan for the running cost of the runs next year's plan will smooth toward but the cash kept
    cannot pay for, at no more than the yearly return those runs earn on that cost. None when a run earns
    nothing or the cash covers them."""
    paid_now = unit_cost.variable_cost_per_run(recipe, inputs, wages)
    if not math.isfinite(paid_now) or paid_now <= 0.0 or revenue_per_run <= paid_now:
        return None
    smoothed = within_a_years_change(replaced(producer, last_runs=worked, capacity_runs=capacity),
                                     capacity * paying)
    short_runs = smoothed - cash_kept / paid_now
    if short_runs <= 0.0:
        return None
    amount = short_runs * paid_now
    return LoanRequest(producer.agent_id, currency, amount, credit.earnable_rate(revenue_per_run - paid_now, paid_now), 1.0, amount,
                       WORKING_CAPITAL_PURPOSE)


def _dividend(producer: Producer, currency: str, amount: float) -> Tuple[Transfer, ...]:
    if amount <= 0.0:
        return ()
    return (Transfer(producer.agent_id, producer.owner, currency, amount, "dividend"),)


def _expansion(producer, recipe, view, currency, rate, capacity, worked, inputs, wages, price_share_after=None):
    """A loan to grow, when a run of new capacity would earn more than the live rate at the price expected
    once the new capacity's output is on the market. Plant that wore out is rebuilt from the producer's own
    cash (the economy's year does it). Only a recipe with plant needs one; without plant the site and the
    owner bound it."""
    value = unit_cost.plant_value_per_run(recipe, inputs, wages)
    if recipe.plant_life_years <= 0.0 or value <= 0.0 or not math.isfinite(value):
        return None, 0.0
    # plant is built for the runs next year can work beyond the capacity left standing, not for idle capacity
    scale = max(worked, producer.expected_sales)
    runs = min(EXPANSION_SHARE_PER_YEAR * producer.capacity_runs,
               scale + OUTPUT_CHANGE_SHARE_PER_YEAR * producer.capacity_runs - capacity)
    if runs <= 0.0:
        return None, 0.0
    prices = expected_output_prices(producer, recipe, view) or {}
    if price_share_after is not None:
        if unit_cost.return_on_capital(recipe, prices, inputs, wages) <= rate:
            return None, 0.0        # the price can only fall with the addition, so the return cannot beat the rate
        prices = {good: price * price_share_after(good, runs * recipe.outputs[good] * producer.yield_factor)
                  for good, price in prices.items()}
    yearly_return = unit_cost.return_on_capital(recipe, prices, inputs, wages)
    if yearly_return <= rate:
        return None, 0.0
    amount = runs * value
    return LoanRequest(producer.agent_id, currency, amount, credit.earnable_rate(yearly_return), recipe.plant_life_years,
                       amount, "expand"), runs
