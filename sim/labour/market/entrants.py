"""The coming-of-age cohort chooses a trade, band by band (DESIGN.md, step 4).

A person weighs each trade by the present value of its expected income after training, discounted by the
chance of not finishing (then the fallback trade's income applies), plus the log of how many jobs the
trade has in the area (a size term: a trade with many places is found and chosen by many, one nobody
employs by almost nobody, however many trades the registry lists). Choice is a logit; applicants beyond
a trade's places re-choose among trades that still have places, and last go to the fallback trade.
"""
import math
from typing import Dict, List, Mapping

from sim.constants import declare

from . import aptitude, expectations, training
from .records import MarketState, YearInputs, YearReport
from .trades import fallback_trade

ENTRANT_TASTE_SCALE_YEARS_OF_SUBSISTENCE = declare(
    "ENTRANT_TASTE_SCALE_YEARS_OF_SUBSISTENCE", 3.0, kind="temporary_heuristic",
    unit="years of an area's subsistence income per e-fold of choice odds", source=None, confidence="D",
    why="How sharply entrants follow the lifetime value of a trade; the rest is taste, family and "
        "information they lack. Not fitted; to be derived from household information and kinship ties.")

OPEN_PLACES_TOLERANCE = 1e-9   # people; places below this count as none
JOBS_FLOOR = 1e-6               # workers' worth of jobs a trade with none is still counted as having


def _jobs(clearings: Mapping, area: str, trade: str, hours_per_worker_year: float) -> float:
    """Workers' worth of jobs a trade has in an area this year: hours hired plus hours left vacant."""
    clearing = clearings.get((area, trade))
    if clearing is None or hours_per_worker_year <= 0.0:
        return JOBS_FLOOR
    return max(JOBS_FLOOR, (clearing.hours_hired + clearing.vacant_hours) / hours_per_worker_year)


def _candidates(inputs: YearInputs) -> List[str]:
    allowed = inputs.enterable_trades
    return sorted(trade for trade in inputs.trades if allowed is None or trade in allowed)


def place_entrants(state: MarketState, inputs: YearInputs, clearings: Mapping, report: YearReport) -> None:
    """The year's entrants choose in rounds; each round sees the places the earlier rounds took."""
    rounds = int(expectations.DECISION_ROUNDS_PER_YEAR)
    for area in sorted(inputs.entrants):
        people = inputs.entrants[area] / rounds
        if people <= 0.0:
            continue
        for _round in range(rounds):
            _place_round(state, inputs, clearings, area, people, report)


def _place_round(state: MarketState, inputs: YearInputs, clearings: Mapping, area: str, people: float,
                 report: YearReport) -> None:
    fallback = fallback_trade(inputs.trades)
    abilities = aptitude.band_abilities()
    candidates = _candidates(inputs)
    if fallback not in candidates:
        candidates.append(fallback)
    income = {trade: expectations.income_at_graduation(
                  state, inputs, clearings, area, trade,
                  aptitude.completion_by_band(inputs.trades[trade].difficulty))
              for trade in candidates}
    subsistence = inputs.subsistence_per_worker_year.get(area, 0.0)
    reference = subsistence if subsistence > 0.0 else (income[fallback] if income[fallback] > 0.0 else 1.0)
    scale = ENTRANT_TASTE_SCALE_YEARS_OF_SUBSISTENCE * reference
    values = _band_values(inputs, abilities, candidates, income, fallback)
    size_terms = {trade: scale * math.log(_jobs(clearings, area, trade, inputs.hours_per_worker_year))
                  for trade in candidates}
    values = [{trade: value + size_terms[trade] for trade, value in by_trade.items()} for by_trade in values]
    waiting = aptitude.split_evenly(people)
    entered: Dict[str, float] = {}
    open_trades = candidates
    for _attempt in range(len(candidates)):
        if aptitude.band_total(waiting) <= 0.0 or not open_trades:
            break
        wanting = _wanting(waiting, values, open_trades, scale)
        waiting = aptitude.empty_bands()
        for trade in open_trades:
            bands = wanting[trade]
            if aptitude.band_total(bands) <= 0.0:
                continue
            refused = training.enrol(state, inputs, area, trade, bands)
            entered[trade] = entered.get(trade, 0.0) + aptitude.band_total(bands) - aptitude.band_total(refused)
            aptitude.add_bands(waiting, refused)
        open_trades = [trade for trade in open_trades
                       if training.open_places(state, inputs, area, trade) > OPEN_PLACES_TOLERANCE]
    leftover = aptitude.band_total(waiting)
    if leftover > 0.0:
        aptitude.add_bands(aptitude.bands_of(state.workers.setdefault(area, {}), fallback), waiting)
        entered[fallback] = entered.get(fallback, 0.0) + leftover
    for trade, count in entered.items():
        report.entered.setdefault(area, {})[trade] = report.entered.get(area, {}).get(trade, 0.0) + count


def _band_values(inputs: YearInputs, abilities: List[float], candidates: List[str],
                 income: Mapping[str, float], fallback: str) -> List[Dict[str, float]]:
    rate = inputs.discount_rate
    career = inputs.career_years
    values: List[Dict[str, float]] = []
    for ability in abilities:
        by_trade: Dict[str, float] = {}
        for trade in candidates:
            spec = inputs.trades[trade]
            chance = aptitude.completion_chance(ability, spec.difficulty)
            start = spec.training_years
            by_trade[trade] = (
                chance * expectations.present_value(income[trade], rate, start, career)
                + (1.0 - chance) * expectations.present_value(income[fallback], rate, start, career))
        values.append(by_trade)
    return values


def _wanting(waiting: List[float], values: List[Dict[str, float]], trades: List[str],
             scale: float) -> Dict[str, List[float]]:
    wanting = {trade: aptitude.empty_bands() for trade in trades}
    for band, count in enumerate(waiting):
        if count <= 0.0:
            continue
        shares = expectations.logit_shares({trade: values[band][trade] for trade in trades}, scale)
        for trade in trades:
            wanting[trade][band] = count * shares[trade]
    return wanting
