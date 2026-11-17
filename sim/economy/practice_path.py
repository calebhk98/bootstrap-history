"""The learning path of a crew: the hours and the usable output its runs average over the years the workshop expects to keep the trade.

A crew with little practice needs several times the booked hours this year (`practice.hours_multiplier`) and spoils part of its
output (`practice.usable_output_share`), but its runs advance its practice (`practice.crew_runs_after_year`), so a run's cost falls
year by year to the booked one. A producer that judges whether to work on this year's cost alone never runs, so never practises.
`learning_path_scales` is the discounted mean over the horizon of the hours multiplier of each trade and of the usable share; the
plan weighs a run by it (`plan_level.py`) and the entry decision takes the same hours (`entry_practice.planned_recipe`).
"""
import math
from typing import Dict, Mapping, Tuple

from sim.constants import declare

from . import practice

YEARS_A_WORKSHOP_EXPECTS_TO_KEEP_A_TRADE = declare(
    "YEARS_A_WORKSHOP_EXPECTS_TO_KEEP_A_TRADE", 20, kind="temporary_heuristic", unit="years", source=None, confidence="D",
    retire="Complaints/644: per-worker skill held by the labour market; then the owner's working life and the plant's life give the horizon",
    why="A workshop weighs the hours its crew needs while learning against the years it will work the trade at the floor. How "
        "long an owner expects to keep a trade is not modelled; a recipe with plant holds it to the plant's life. No source "
        "found for a figure: Wallis (LSE Economic History WP 22/07, pp. 23-24) gives apprenticeship terms of several years, "
        "the learner's term and not the master's horizon.")


def horizon_years(plant_life_years: float) -> int:
    """Whole years a workshop expects to keep a trade: `YEARS_A_WORKSHOP_EXPECTS_TO_KEEP_A_TRADE`, held to the plant's life
    where the recipe has plant (a life of zero is no plant); at least one."""
    kept = float(YEARS_A_WORKSHOP_EXPECTS_TO_KEEP_A_TRADE)
    if plant_life_years > 0.0:
        kept = min(kept, plant_life_years)
    return max(1, int(round(kept)))


def learning_path_scales(units_by_trade: Mapping[str, float], booked_hours: Mapping[str, float], runs_per_workshop_per_year: float,
                         horizon: int, discount_rate: float) -> Tuple[Dict[str, float], float]:
    """(each trade's hours multiplier, the usable-output share) averaged over `horizon` years, a later year weighted by one over
    one plus `discount_rate` to the years elapsed. The crew starts at `units_by_trade` (a trade with no entry is at the floor) and
    gains `runs_per_workshop_per_year` a year as `practice.crew_runs_after_year` adds them. `booked_hours` is the recipe's hours
    by trade, which the share needs. A crew at the floor gives one and one; one year gives this year's multipliers and share."""
    rate = max(0.0, discount_rate)
    trades = sorted(booked_hours)
    booked_total = math.fsum(booked_hours.values())
    crew = {trade: units_by_trade[trade] for trade in trades if trade in units_by_trade}
    weights, multipliers, shares = [], {trade: [] for trade in trades}, []
    for year in range(max(1, horizon)):
        weights.append((1.0 + rate) ** -year)
        practised = 0.0
        for trade in trades:
            multiplier = practice.hours_multiplier(crew[trade]) if trade in crew else 1.0
            multipliers[trade].append(multiplier)
            practised += booked_hours[trade] * multiplier
        shares.append(practice.usable_output_share(booked_total, practised))
        crew = practice.crew_runs_after_year(crew, runs_per_workshop_per_year, 0.0, {})
    total = math.fsum(weights)

    def mean(values):
        return math.fsum(weight * value for weight, value in zip(weights, values)) / total
    return {trade: mean(each) for trade, each in multipliers.items()}, mean(shares)
