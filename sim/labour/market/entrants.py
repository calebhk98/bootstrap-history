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

NEGLIGIBLE_CHOICE_SHARE = declare(
    "NEGLIGIBLE_CHOICE_SHARE", 1e-6, kind="temporary_heuristic", unit="share of the people choosing",
    source=None, confidence="D",
    why="A trade that fewer than this share of a round's choosers pick is not enrolled in; its few go to the "
        "trade most of them chose. Every trade has some logit weight, and enrolling a speck in each makes a "
        "cohort record per trade per round. Not fitted.")

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
        _place_area(state, inputs, clearings, area, people, rounds, report)


def _place_area(state: MarketState, inputs: YearInputs, clearings: Mapping, area: str, people: float,
                rounds: int, report: YearReport) -> None:
    """All rounds of one area. Only enrolling changes what a trade pays at graduation, so later rounds
    re-weigh just the trades that took people in the round before."""
    fallback = fallback_trade(inputs.trades)
    candidates = _candidates(inputs)
    if fallback not in candidates:
        candidates.append(fallback)
    subsistence = inputs.subsistence_per_worker_year.get(area, 0.0)
    income: Dict[str, float] = {}
    values: Dict[str, List[float]] = {}   # per trade, its worth to each band (size term included)
    scale = 0.0
    size_terms: Dict[str, float] = {}
    stale = candidates   # trades whose income must be re-read
    for _round in range(rounds):
        fresh = {trade: expectations.income_at_graduation(
                     state, inputs, clearings, area, trade,
                     aptitude.completion_by_band(inputs.trades[trade].difficulty))
                 for trade in stale}
        if not income:
            reference = subsistence if subsistence > 0.0 else (fresh[fallback] if fresh[fallback] > 0.0 else 1.0)
            scale = ENTRANT_TASTE_SCALE_YEARS_OF_SUBSISTENCE * reference
            size_terms = {trade: scale * math.log(_jobs(clearings, area, trade, inputs.hours_per_worker_year))
                          for trade in candidates}
        elif fresh.get(fallback, income[fallback]) != income[fallback]:
            fresh = {trade: fresh[trade] if trade in fresh else expectations.income_at_graduation(
                         state, inputs, clearings, area, trade,
                         aptitude.completion_by_band(inputs.trades[trade].difficulty))
                     for trade in candidates}
        income.update(fresh)
        values.update(_band_values(inputs, list(fresh), income, fallback, size_terms))
        taken = _place_round(state, inputs, area, people, report, candidates, values, scale, fallback)
        stale = [trade for trade in candidates if trade in taken]


def _place_round(state: MarketState, inputs: YearInputs, area: str, people: float, report: YearReport,
                 candidates: List[str], values: Mapping[str, List[float]], scale: float, fallback: str) -> set:
    """One round of choices; returns the trades that took people."""
    waiting = aptitude.split_evenly(people)
    entered: Dict[str, float] = {}
    open_trades = candidates
    places: Dict[str, float] = {}   # open places by trade; only a trade that took people changes
    for _attempt in range(len(candidates)):
        if aptitude.band_total(waiting) <= 0.0 or not open_trades:
            break
        wanting = _wanting(waiting, values, open_trades, scale)
        _fold_specks(wanting, aptitude.band_total(waiting) * NEGLIGIBLE_CHOICE_SHARE)
        waiting = aptitude.empty_bands()
        for trade in open_trades:
            bands = wanting[trade]
            if aptitude.band_total(bands) <= 0.0:
                continue
            refused = training.enrol(state, inputs, area, trade, bands)
            places.pop(trade, None)
            entered[trade] = entered.get(trade, 0.0) + aptitude.band_total(bands) - aptitude.band_total(refused)
            aptitude.add_bands(waiting, refused)
        for trade in open_trades:
            if trade not in places:
                places[trade] = training.open_places(state, inputs, area, trade)
        open_trades = [trade for trade in open_trades if places[trade] > OPEN_PLACES_TOLERANCE]
    leftover = aptitude.band_total(waiting)
    if leftover > 0.0:
        aptitude.add_bands(aptitude.bands_of(state.workers.setdefault(area, {}), fallback), waiting)
        entered[fallback] = entered.get(fallback, 0.0) + leftover
    record = report.entered.setdefault(area, {})
    for trade, count in entered.items():
        record[trade] = record.get(trade, 0.0) + count
    return set(entered)


def _band_values(inputs: YearInputs, trades: List[str], income: Mapping[str, float], fallback: str,
                 size_terms: Mapping[str, float]) -> Dict[str, List[float]]:
    """For each trade, what it is worth to a person of each band: the present value of its income after
    training weighted by the chance of finishing (else the fallback's), plus the size term."""
    rate = inputs.discount_rate
    career = inputs.career_years
    values: Dict[str, List[float]] = {}
    for trade in trades:
        spec = inputs.trades[trade]
        start = spec.training_years
        success = expectations.present_value(income[trade], rate, start, career)
        failure = expectations.present_value(income[fallback], rate, start, career)
        size = size_terms[trade]
        values[trade] = [chance * success + (1.0 - chance) * failure + size
                         for chance in aptitude.completion_by_band(spec.difficulty)]
    return values


def _wanting(waiting: List[float], values: Mapping[str, List[float]], trades: List[str],
             scale: float) -> Dict[str, List[float]]:
    """People of each band choosing each trade: a logit over the trades, weighted by what each is worth."""
    wanting = {trade: aptitude.empty_bands() for trade in trades}
    columns = [values[trade] for trade in trades]
    exp = math.exp
    fsum = math.fsum
    for band, count in enumerate(waiting):
        if count <= 0.0:
            continue
        scores = [column[band] for column in columns]
        top = max(scores)
        weights = [exp((score - top) / scale) for score in scores]
        total = fsum(weights)
        for trade, weight in zip(trades, weights):
            wanting[trade][band] = count * (weight / total)
    return wanting


def _fold_specks(wanting: Dict[str, List[float]], cutoff: float) -> None:
    """Trades chosen by fewer people than `cutoff` give their few to the most chosen trade."""
    totals = {trade: math.fsum(bands) for trade, bands in wanting.items()}
    biggest = max(totals, key=totals.get)
    for trade, total in totals.items():
        if total < cutoff and trade != biggest:
            aptitude.add_bands(wanting[biggest], wanting[trade])
            wanting[trade] = aptitude.empty_bands()
