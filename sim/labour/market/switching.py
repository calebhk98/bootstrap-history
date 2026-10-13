"""Workers re-weigh their trade against the others, with a stay option (DESIGN.md, step 5).

A switcher becomes a trainee of the new trade (shorter within a skill family) through the same places
as entrants; those not admitted stay in their old trade. The fallback trade takes people straight in.
"""
import math
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


NEGLIGIBLE_MOVE_SHARE = declare(
    "NEGLIGIBLE_MOVE_SHARE", 1e-3, kind="temporary_heuristic", unit="share of the workers weighing a switch",
    source=None, confidence="D",
    why="A destination that fewer than this share of the workers weighing a switch would pick is not trained "
        "for; its few go to the destination most of them pick. Every destination has some logit weight, and "
        "training a few for each costs a cohort record apiece. Not fitted.")

PLAN_REUSE_TOLERANCE = declare(
    "PLAN_REUSE_TOLERANCE", 0.01, kind="temporary_heuristic",
    unit="years of an area's subsistence income", source=None, confidence="D",
    why="A later round of switching keeps the choice odds of the round before when no destination's "
        "income after training has moved by more than this; saves re-weighing every trade for a change "
        "too small to alter anyone's choice. Not fitted.")


def switch_trades(state: MarketState, inputs: YearInputs, clearings: Mapping, report: YearReport) -> None:
    allowed = inputs.enterable_trades
    destinations = sorted(trade for trade in inputs.trades if allowed is None or trade in allowed)
    rounds = int(expectations.DECISION_ROUNDS_PER_YEAR)
    chances = {trade: aptitude.completion_by_band(inputs.trades[trade].difficulty) for trade in destinations}
    for area in sorted(state.workers):
        subsistence = inputs.subsistence_per_worker_year.get(area, 0.0)
        if subsistence <= 0.0:
            continue
        sources = [trade for trade in sorted(state.workers[area])
                   if trade in inputs.trades and aptitude.band_total(state.workers[area][trade]) > 0.0]
        if not sources:
            continue
        income = {trade: expectations.expected_income(state, inputs, clearings, area, trade)
                  for trade in sources}
        vacancies = {trade for trade in destinations
                     if (area, trade) in clearings and clearings[(area, trade)].vacant_hours > 0.0}
        later_income: Dict[str, float] = {}
        planned: Dict[str, tuple] = {}   # source -> (later income it was planned on, odds of each target per band)
        stale = destinations   # trades whose income after training must be re-read (enrolling changes it)
        for _round in range(rounds):
            for trade in stale:
                later_income[trade] = expectations.income_at_graduation(state, inputs, clearings, area, trade,
                                                                        chances[trade])
            moves = _planned_moves(state, inputs, area, sources, destinations, income, later_income, vacancies,
                                   subsistence, chances, planned)
            stale = _carry_out(state, inputs, report, area, moves)


def _odds(inputs, state, area, source, destinations, income, later_income, vacancies, subsistence, chances):
    """The odds of each band of `source` workers moving to each worthwhile destination: (targets, per
    band the share of each target), or None for a band that stays."""
    rate = inputs.discount_rate
    remaining = inputs.career_years * REMAINING_CAREER_SHARE
    own = income[source]
    targets = [trade for trade in destinations if trade != source
               and (later_income[trade] > own or trade in vacancies)]
    if not targets:
        return None
    gain = []
    lost = []
    for trade in targets:
        years = inputs.trades[trade].training_years * _training_share(inputs, source, trade)
        lost.append(own * expectations.annuity_factor(rate, years))
        gain.append(expectations.present_value(later_income[trade] - own, rate, years, remaining))
    bands = []
    exp = math.exp
    for band, count in enumerate(state.workers[area][source]):
        scores = []
        picked = []
        for index, trade in enumerate(targets):
            score = (chances[trade][band] * gain[index] - lost[index]) / subsistence
            if score > 0.0:   # a move worth less than staying is not considered at all
                scores.append(score)
                picked.append(index)
        if not scores:
            bands.append(None)
            continue
        top = max(scores)
        scale = SWITCHING_TASTE_SCALE
        weights = [exp((score - top) / scale) for score in scores]
        total = math.fsum(weights + [exp((0.0 - top) / scale)])   # the last is staying
        cutoff = total * NEGLIGIBLE_MOVE_SHARE
        leader = weights.index(max(weights))
        shares = [weight / total if weight >= cutoff else 0.0 for weight in weights]
        shares[leader] += math.fsum(weight for weight in weights if weight < cutoff) / total
        bands.append([(targets[index], share) for index, share in zip(picked, shares) if share > 0.0])
    return targets, bands


def _plan_still_holds(then: Mapping[str, float], later_income: Mapping[str, float], income_here: float,
                      odds, vacancies, destinations, tolerance: float) -> bool:
    """Whether no destination's income after training has moved enough to change a source's odds."""
    targets = () if odds is None else odds[0]
    for trade in destinations:
        if abs(later_income[trade] - then[trade]) <= tolerance:
            continue
        # a destination that moved matters if it is a target, or has risen past what the source earns
        if trade in targets or later_income[trade] > income_here or trade in vacancies:
            return False
    return True


def _planned_moves(state, inputs, area, sources, destinations, income, later_income, vacancies,
                   subsistence, chances, planned) -> List[Move]:
    moves: List[Move] = []
    rounds = expectations.DECISION_ROUNDS_PER_YEAR
    tolerance = PLAN_REUSE_TOLERANCE * subsistence
    snapshot = None
    for source in sources:
        kept = planned.get(source)
        if kept is not None and _plan_still_holds(kept[0], later_income, income[source], kept[1], vacancies,
                                                  destinations, tolerance):
            odds = kept[1]
        else:
            odds = _odds(inputs, state, area, source, destinations, income, later_income, vacancies, subsistence,
                         chances)
            if snapshot is None:
                snapshot = dict(later_income)
            planned[source] = (snapshot, odds)
        if odds is None:
            continue
        _targets, bands = odds
        source_bands = state.workers[area][source]
        rows: Dict[str, List[float]] = {}
        for band, count in enumerate(source_bands):
            shares = bands[band]
            if count <= 0.0 or shares is None:
                continue
            base = count * SWITCHING_CONSIDERATION_SHARE_PER_YEAR / rounds
            for trade, share in shares:
                row = rows.get(trade)
                if row is None:
                    row = rows[trade] = aptitude.empty_bands()
                row[band] = base * share
        for trade, row in rows.items():
            moves.append((source, trade, row))
    return moves


def _carry_out(state: MarketState, inputs: YearInputs, report: YearReport, area: str,
               moves: List[Move]) -> List[str]:
    """Take the switchers out of their trades and into training. Sources moving to one target on the
    same training length apply together, and the target's places are shared out between them in
    proportion to the people each sends (band by band). Returns the trades that took trainees in."""
    workers = state.workers[area]
    net: Dict[str, float] = {}
    groups: Dict[Tuple[str, float], List[Tuple[str, List[float]]]] = {}
    for source, target, bands in sorted(moves, key=_move_order):
        source_bands = workers[source]
        taken = [value if value < have else have for value, have in zip(bands, source_bands)]
        source_bands[:] = [have - value for have, value in zip(source_bands, taken)]
        groups.setdefault((target, _training_share(inputs, source, target)), []).append((source, taken))
    for (target, share), senders in groups.items():
        if len(senders) == 1:
            combined = senders[0][1]
        else:
            combined = [math.fsum(column) for column in zip(*[taken for _source, taken in senders])]
        refused = training.enrol(state, inputs, area, target, combined, share)
        anything_refused = any(refused)
        for source, taken in senders:
            moved = aptitude.band_total(taken)
            if anything_refused:
                if len(senders) == 1:
                    returned = refused
                else:
                    returned = [back * mine / total if total > 0.0 else 0.0
                                for back, mine, total in zip(refused, taken, combined)]
                aptitude.add_bands(workers[source], returned)
                moved -= aptitude.band_total(returned)
            net[target] = net.get(target, 0.0) + moved
            net[source] = net.get(source, 0.0) - moved
    if net:
        record = report.switched.setdefault(area, {})
        for trade, change in net.items():
            record[trade] = record.get(trade, 0.0) + change
    return [target for target, _share in groups]


def _move_order(move: Move):
    return move[1], move[0]
