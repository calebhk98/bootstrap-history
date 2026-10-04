"""Workers re-weigh their trade against the others, with a stay option (DESIGN.md, step 5).

A switcher becomes a trainee of the new trade (shorter within a skill family) through the same places
as entrants; those not admitted stay in their old trade. The fallback trade takes people straight in.
"""
from typing import Dict, List, Mapping, Tuple

from sim.constants import declare

from . import aptitude, expectations, training
from .records import MarketState, YearInputs, YearReport

RETRAINING_SHARE_WITHIN_FAMILY = declare(
    "RETRAINING_SHARE_WITHIN_FAMILY", 0.3, kind="temporary_heuristic",
    unit="share of a trade's full training years", source=None, confidence="D",
    why="Someone already skilled in a trade's family (same materials, tools and habits) learns a related "
        "trade faster than a newcomer. Not fitted; to be derived from the skills the two trades share.")

REMAINING_CAREER_SHARE = declare(
    "REMAINING_CAREER_SHARE", 0.5, kind="temporary_heuristic",
    unit="share of a full career still ahead of a worker weighing a switch", source=None, confidence="D",
    why="Workers are spread across their careers, so on average half remains. Replace with the age "
        "structure when workers carry an age.")

SWITCHING_TASTE_SCALE = declare(
    "SWITCHING_TASTE_SCALE", 1.0, kind="temporary_heuristic",
    unit="years of an area's subsistence income per e-fold of choice odds", source=None, confidence="D",
    why="How sharply considering workers follow the gain of a switch. Not fitted.")

SWITCHING_CONSIDERATION_SHARE_PER_YEAR = declare(
    "SWITCHING_CONSIDERATION_SHARE_PER_YEAR", 0.05, kind="temporary_heuristic",
    unit="share of a trade's workers who reconsider it in a year", source=None, confidence="D",
    why="Most workers do not weigh a change of trade in any year (ties, custom, lack of information); "
        "this caps yearly switching. Not fitted.")

Move = Tuple[str, str, List[float]]   # source trade, destination trade, people per band


def _training_share(inputs: YearInputs, source: str, target: str) -> float:
    same_family = inputs.trades[source].family == inputs.trades[target].family
    return RETRAINING_SHARE_WITHIN_FAMILY if same_family else 1.0


def switch_trades(state: MarketState, inputs: YearInputs, clearings: Mapping, report: YearReport) -> None:
    abilities = aptitude.band_abilities()
    allowed = inputs.enterable_trades
    destinations = sorted(trade for trade in inputs.trades if allowed is None or trade in allowed)
    for area in sorted(state.workers):
        subsistence = inputs.subsistence_per_worker_year.get(area, 0.0)
        if subsistence <= 0.0:
            continue
        sources = [trade for trade in sorted(state.workers[area])
                   if trade in inputs.trades and aptitude.band_total(state.workers[area][trade]) > 0.0]
        if not sources:
            continue
        income = {trade: expectations.expected_income(state, inputs, clearings, area, trade)
                  for trade in set(destinations) | set(sources)}
        vacancies = {trade for trade in destinations
                     if (area, trade) in clearings and clearings[(area, trade)].vacant_hours > 0.0}
        moves = _planned_moves(state, inputs, area, sources, destinations, income, vacancies,
                               abilities, subsistence)
        _carry_out(state, inputs, report, area, moves)


def _planned_moves(state, inputs, area, sources, destinations, income, vacancies, abilities,
                   subsistence) -> List[Move]:
    rate = inputs.discount_rate
    remaining = inputs.career_years * REMAINING_CAREER_SHARE
    moves: List[Move] = []
    for source in sources:
        targets = [trade for trade in destinations if trade != source
                   and (income[trade] > income[source] or trade in vacancies)]
        if not targets:
            continue
        gain: Dict[str, float] = {}
        lost: Dict[str, float] = {}
        for trade in targets:
            years = inputs.trades[trade].training_years * _training_share(inputs, source, trade)
            lost[trade] = income[source] * expectations.annuity_factor(rate, years)
            gain[trade] = expectations.present_value(income[trade] - income[source], rate, years, remaining)
        by_target = {trade: aptitude.empty_bands() for trade in targets}
        for band, count in enumerate(state.workers[area][source]):
            if count <= 0.0:
                continue
            scores = {"": 0.0}   # staying; trade ids are never empty
            for trade in targets:
                chance = aptitude.completion_chance(abilities[band], inputs.trades[trade].difficulty)
                scores[trade] = (chance * gain[trade] - lost[trade]) / subsistence
            shares = expectations.logit_shares(scores, SWITCHING_TASTE_SCALE)
            for trade in targets:
                by_target[trade][band] = count * SWITCHING_CONSIDERATION_SHARE_PER_YEAR * shares[trade]
        for trade in targets:
            if aptitude.band_total(by_target[trade]) > 0.0:
                moves.append((source, trade, by_target[trade]))
    return moves


def _carry_out(state: MarketState, inputs: YearInputs, report: YearReport, area: str,
               moves: List[Move]) -> None:
    workers = state.workers[area]
    net: Dict[str, float] = {}
    for source, target, bands in sorted(moves, key=lambda move: (move[1], move[0])):
        source_bands = workers[source]
        taken = [min(value, have) for value, have in zip(bands, source_bands)]
        for index, value in enumerate(taken):
            source_bands[index] -= value
        refused = training.enrol(state, inputs, area, target, taken, _training_share(inputs, source, target))
        aptitude.add_bands(source_bands, refused)
        moved = aptitude.band_total(taken) - aptitude.band_total(refused)
        net[target] = net.get(target, 0.0) + moved
        net[source] = net.get(source, 0.0) - moved
    if net:
        record = report.switched.setdefault(area, {})
        for trade, change in net.items():
            record[trade] = record.get(trade, 0.0) + change
