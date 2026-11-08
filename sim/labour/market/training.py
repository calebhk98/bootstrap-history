"""Who is learning a trade, how many places there are to learn it, and who finishes.

A trade is taught by those who already practise it (apprenticeship) and by schools. Places to learn
at once are `incumbent workers * APPRENTICES_PER_MASTER + school seats`; trainees already enrolled
fill them. A trade with no incumbents and no school cannot reproduce. Trainees finish after the
trade's training years with their band's completion chance (aptitude.py); those who do not finish
join the fallback trade. A trade needing no training takes people straight into work.
"""
import math
from typing import List, Sequence, Tuple

import numpy as np

from sim.constants import declare

from . import aptitude, training_kernel
from .records import MarketState, YearInputs, YearReport
from .trades import fallback_trade

APPRENTICES_PER_MASTER = declare(
    "APPRENTICES_PER_MASTER", 0.5, kind="temporary_heuristic",
    unit="trainees taught at once per practising worker of the trade", source=None, confidence="D",
    why="Guilds capped a master at one to three apprentices and most practitioners were journeymen who "
        "took none, so the trade-wide ratio is well under one. Not fitted; to be derived from household "
        "and workshop capacity when that exists.")

GRADUATION_TOLERANCE_YEARS = 1e-9   # float slack when a cohort's remaining years reach zero


def school_places(inputs: YearInputs, area: str, trade: str) -> Tuple[float, float]:
    """School seats teaching this trade here, and their seat-weighted completion bonus."""
    seats = bonus_weight = 0.0
    for school in inputs.schools:
        if school.area == area and school.trade == trade and school.seats > 0.0:
            seats += school.seats
            bonus_weight += school.seats * school.completion_bonus
    return seats, (bonus_weight / seats if seats > 0.0 else 0.0)


def enrolled(state: MarketState, area: str, trade: str) -> float:
    """Trainees already in this trade here, summed over its cohorts."""
    return math.fsum([math.fsum(cohort[1]) for cohort in state.trainees.get(area, {}).get(trade, ())])


def _incumbents(state: MarketState, area: str, trade: str) -> float:
    bands = state.workers.get(area, {}).get(trade)
    return math.fsum(bands) if bands is not None else 0.0


def enrol(state: MarketState, inputs: YearInputs, area: str, trade: str,
          bands: Sequence[float], training_share: float = 1.0) -> List[float]:
    """Take people (per band) into a trade's training here, as far as places allow. Returns, per band,
    those not admitted. `training_share` shortens the training (retraining within a skill family)."""
    wanting = aptitude.band_total(bands)
    if wanting <= 0.0:
        return list(bands)
    spec = inputs.trades[trade]
    years = spec.training_years * max(0.0, training_share)
    if years <= 0.0:
        aptitude.add_bands(aptitude.bands_of(state.workers.setdefault(area, {}), trade), bands)
        return aptitude.empty_bands()
    seats, school_bonus = school_places(inputs, area, trade) if inputs.schools else (0.0, 0.0)
    capacity = seats + _incumbents(state, area, trade) * APPRENTICES_PER_MASTER
    already = enrolled(state, area, trade)
    admitted_share = min(1.0, max(0.0, capacity - already) / wanting)
    if admitted_share <= 0.0:
        return list(bands)
    bonus = school_bonus * (seats / capacity) if capacity > 0.0 else 0.0
    if admitted_share >= 1.0:
        admitted = list(bands)
        refused = aptitude.empty_bands()
    else:
        admitted = [value * admitted_share for value in bands]
        refused = [value - taken for value, taken in zip(bands, admitted)]
    cohorts = state.trainees.setdefault(area, {}).setdefault(trade, [])
    if cohorts and cohorts[-1][0] == years and cohorts[-1][2] == bonus:
        aptitude.add_bands(cohorts[-1][1], admitted)   # same finish date and teaching: one cohort
    else:
        cohorts.append([years, admitted, bonus])
    return refused


def advance(state: MarketState, inputs: YearInputs, report: YearReport) -> None:
    """Every cohort ages a year; finished cohorts graduate or fall back (`training_kernel.age_cohorts` over the trainees table)."""
    fallback = fallback_trade(inputs.trades)
    state.admit((), list(inputs.trades))
    rows = int(state.trainee_table.row_count[0])
    if not rows:
        return
    ids = state.ids
    specs = [inputs.trades.get(name) for name in ids.trades.names]
    difficulty = np.array([spec.difficulty if spec else 0.0 for spec in specs])
    has_spec = np.array([spec is not None for spec in specs], np.bool_)
    trainees, workers, areas = state.trainee_table, state.workers_table, state.areas_table
    keep = np.zeros(rows, np.bool_)
    graduated, graduated_any = np.zeros(len(workers.present)), np.zeros(len(workers.present), np.bool_)
    counter = np.array([state._order], np.int64)
    training_kernel.age_cohorts(trainees.market, trainees.years_left, trainees.bonus, trainees.people, rows, len(ids.trades), difficulty, has_spec,
                                ids.trades.number(fallback), np.array(aptitude.band_abilities()), aptitude.COMPLETION_SPREAD,
                                GRADUATION_TOLERANCE_YEARS, workers.people, workers.present, workers.order, workers.length, areas.workers_named,
                                areas.workers_order, counter, graduated, graduated_any, keep)
    state._order = int(counter[0])
    state.keep_cohorts(keep)
    trade_count = len(ids.trades)
    for row in np.flatnonzero(graduated_any).tolist():
        area, trade = ids.areas.names[row // trade_count], ids.trades.names[row % trade_count]
        report.graduated.setdefault(area, {})[trade] = report.graduated.get(area, {}).get(trade, 0.0) + float(graduated[row])
