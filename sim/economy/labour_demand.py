"""A producer's demand for hours as a schedule over the wage: the labour bids of the clearing rule set.

A producer stands for many workplaces whose costs spread around its own (`producers.COST_SPREAD_WITHIN_PRODUCER`, the
spread `producers.share_working` reads). A workplace works while a run's revenue covers its cost, so each slice of the
workplaces, cheapest first, is worth hiring up to the wage at which its dearest workplace breaks even. Bidding the
slices one by one lets the labour market find, inside the year, the wage and the hours together: a producer that would
plan fewer runs at a higher wage says so in its bids, and does not wait a year to find out."""
import dataclasses
import math
from statistics import NormalDist
from typing import List, Optional, Tuple

from sim.constants import declare

from . import practice, unit_cost
from .labour_ceilings import joint_labour_ceilings
from .producers import (COST_SPREAD_WITHIN_PRODUCER, Producer, expected_input_prices, kept_output_prices, live_input_prices,
                        live_wages, next_years_runs_ceiling, paid_input_prices, runs_for_stock, share_working, with_practised_yield)
from .types import LabourBid, Recipe

LABOUR_DEMAND_SLICES = declare(
    "LABOUR_DEMAND_SLICES", 8, kind="temporary_heuristic", unit="slices of a producer's workplaces, each bid for at its own worth",
    source=None, confidence="D",
    retire="no complaint covers it; retired when the labour core takes a producer's demand as a curve and not as steps",
    why="How finely the falling worth of a producer's hours is cut into bids. More slices follow the curve more closely "
        "and cost more bids to clear; the clearing interpolates between steps, so a few are enough. Not fitted.")

_STANDARD_NORMAL = NormalDist()


def cost_multiple_at(share_of_workplaces: float, spread: float = COST_SPREAD_WITHIN_PRODUCER) -> float:
    """A workplace's cost over the producer's own cost, for the workplace that this share of the workplaces are cheaper
    than: the log-normal spread `producers.share_working` reads, turned round."""
    return math.exp(spread * _STANDARD_NORMAL.inv_cdf(share_of_workplaces) - spread * spread / 2.0)


def slice_worths(capacity_runs: float, most_runs: float, revenue_per_run: float, other_cost_per_run: float,
                 slices: int = LABOUR_DEMAND_SLICES) -> List[Tuple[float, float]]:
    """[(runs, money a run leaves for its hours)] for the slices of the producer's workplaces up to `most_runs`, cheapest
    first: a slice's runs are an equal part of `most_runs`, and what a run of it leaves for its hours is the revenue
    over the cost multiple of the slice's cheapest workplace (the middle one for the first slice, whose cheapest costs
    next to nothing) less the run's other costs. Slices that leave nothing for their hours are left out."""
    top = min(capacity_runs, most_runs)
    if top <= 0.0 or capacity_runs <= 0.0 or revenue_per_run <= 0.0:
        return []
    width = top / slices
    worths = []
    for index in range(slices):
        share = (0.5 if index == 0 else index) * width / capacity_runs
        room = revenue_per_run / cost_multiple_at(share) - other_cost_per_run
        if room <= 0.0:
            break
        worths.append((width, room))
    return worths


def most_runs_wanted(producer: Producer, cash: float, paid_now_per_run: float, held_input_value: float,
                     runs_its_stock_calls_for: float = math.inf) -> float:
    """The most runs the producer would staff whatever the wage: no more than a year's growth beyond its working scale,
    what its stock calls for (`producers.runs_for_stock` read against the runs that pay), what its cash and held
    inputs pay for, and its land."""
    most = min(producer.capacity_runs, next_years_runs_ceiling(producer), runs_its_stock_calls_for)
    if paid_now_per_run > 0.0:
        most = min(most, (max(cash, 0.0) + held_input_value) / paid_now_per_run)
    if producer.land_run_cap is not None:
        most = min(most, producer.land_run_cap)
    return max(0.0, most)


def schedule_bids(producer: Producer, recipe: Recipe, view, cash: float) -> List[LabourBid]:
    """The producer's bids for the year's hours, one per slice of its workplaces and trade (`slice_worths`); none for a
    producer that is idle or whose run brings in nothing."""
    if producer.idle_years > 0 or producer.capacity_runs <= 0.0:
        return []
    producer = with_practised_yield(producer, recipe)
    recipe = practice.recipe_for(recipe, producer.crew_runs)
    outputs = kept_output_prices(producer, recipe, view)
    market_inputs = paid_input_prices(producer, recipe, view, live_input_prices(producer, recipe, view))
    inputs = expected_input_prices(producer, recipe, view, market_inputs)
    wages = live_wages(producer, recipe, view)
    revenue = unit_cost.revenue_per_run(recipe, outputs) * producer.yield_factor
    input_cost = unit_cost.input_cost_per_run(recipe, inputs, wages)
    labour_cost = unit_cost.labour_cost_per_run(recipe, wages)
    other_cost = input_cost + producer.land_rent_per_run
    if revenue <= 0.0 or not math.isfinite(other_cost + labour_cost):
        return []
    paying_prices = {**inputs, **market_inputs}
    held_value = sum(min(view.stock(producer.agent_id, good, producer.tile), quantity * producer.capacity_runs) * paying_prices[good]
                     for good, quantity in recipe.inputs.items() if good in paying_prices)
    paid_now = unit_cost.input_cost_per_run(recipe, paying_prices, wages) + labour_cost
    paying = producer.capacity_runs * share_working(revenue, other_cost + labour_cost)
    for_stock = runs_for_stock(dataclasses.replace(producer, expected_sales=paying), recipe, view, other_cost + labour_cost, outputs)
    most = most_runs_wanted(producer, cash, paid_now, held_value, for_stock)
    bids = []
    for runs, room in slice_worths(producer.capacity_runs, most, revenue, other_cost):
        ceilings = joint_labour_ceilings(recipe.labour_hours, wages, room)
        bids.extend(LabourBid(producer.agent_id, trade, view.area_of(trade, producer.tile), runs * recipe.labour_hours[trade],
                              ceilings[trade]) for trade in sorted(recipe.labour_hours) if trade in ceilings)
    return bids


def write_schedule_bids(setup, record, view, plans, bid_table, cash_of: Optional[callable] = None) -> None:
    """Every producer's schedule of labour bids into the year's bid table, in the producers' saved order. `plans` (the
    year's plan table) is not read: the schedule says what the producer would hire at every wage, the plan what it
    expected to at last year's."""
    money = setup.currency_id
    for producer_id in record.producers:
        producer = record.producers[producer_id]
        cash = record.book.balance(producer_id, money) if cash_of is None else cash_of(producer_id)
        bid_table.add_objects(schedule_bids(producer, setup.recipes[producer.recipe_id], view, cash))
