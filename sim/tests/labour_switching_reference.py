"""The plain Python rules of switching's choice odds and planned moves, as they ran before the arrays kernel
(`switching_kernel.plan_area`): kept so a test runs both on the same inputs. Not used by the game."""
import math
from operator import sub
from typing import Dict, List, Mapping, Tuple

import numpy as np

from sim.labour.market import aptitude, expectations, switching_kernel, training
from sim.labour.market.premium import annuity_factor
from sim.labour.market.switching import (NEGLIGIBLE_MOVE_SHARE, REMAINING_CAREER_SHARE,
                                         SWITCHING_CONSIDERATION_SHARE_PER_YEAR, SWITCHING_TASTE_SCALE,
                                         RETRAINING_SHARE_WITHIN_FAMILY)
from sim.tests.labour_switching_plain import Move, _move_order
from sim.labour.market.records import MarketState, YearInputs, YearReport
from sim.labour.market.trades import fallback_trade


def band_odds(chances, gain, lost, unit, stay_score, scale, negligible):
    """`switching_kernel.band_shares` on the targets' scores: (shares[band, target], moves[band])."""
    scores = (np.asarray(chances).T * np.asarray(gain) - np.asarray(lost)) / unit
    targets = scores.shape[1]
    shares, moves = np.zeros(scores.shape), np.zeros(scores.shape[0], np.bool_)
    switching_kernel.band_shares(scores, np.arange(targets), targets, stay_score, scale, negligible, shares, moves, np.empty(targets))
    return shares, moves


def _training_share(inputs: YearInputs, source: str, target: str) -> float:
    same_family = inputs.trades[source].family == inputs.trades[target].family
    return RETRAINING_SHARE_WITHIN_FAMILY if same_family else 1.0


def _odds(inputs, state, area, source, destinations, own, later_income, vacancies, subsistence, chances, young,
          stay_income=None):
    """The odds of each band of `source` workers moving to each other destination: (targets, per band the share of each target),
    or None for a band that stays. `own` is the income given up. Every destination is weighed against staying: the young
    over a whole career, the established over what is left of one. The young may stay in `source`, scored at `stay_income` (what
    it pays now) over the career against `own`; an established worker's stay scores nothing, being the income given up."""
    rate = inputs.discount_rate
    remaining = inputs.career_years if young else inputs.career_years * REMAINING_CAREER_SHARE
    targets = [trade for trade in destinations if trade != source]
    if not targets:
        return None
    gain = []
    lost = []
    for trade in targets:
        years = inputs.trades[trade].training_years * (1.0 if young else _training_share(inputs, source, trade))
        lost.append(own * annuity_factor(rate, years))
        gain.append(expectations.present_value(later_income[trade] - own, rate, years, remaining))
    stay_score = 0.0
    if young and stay_income is not None:
        stay_score = expectations.present_value(stay_income - own, rate, 0.0, remaining) / subsistence
    shares, moves = band_odds(np.array([chances[trade] for trade in targets]), gain, lost, subsistence, stay_score,
                              SWITCHING_TASTE_SCALE, NEGLIGIBLE_MOVE_SHARE)
    bands = [[(trade, share) for trade, share in zip(targets, row) if share > 0.0] if moving else None
             for row, moving in zip(shares.tolist(), moves.tolist())]
    return targets, bands


def _plan_still_holds(then: Mapping[str, float], later_income: Mapping[str, float], destinations) -> bool:
    """Whether no destination's income after training has changed, so a source's odds are the ones it planned on."""
    return all(later_income[trade] == then[trade] for trade in destinations)


def _planned_moves(state, inputs, area, sources, destinations, income, baseline, later_income, vacancies,
                   subsistence, chances, planned, idle) -> List[Move]:
    moves: List[Move] = []
    rounds = expectations.DECISION_ROUNDS_PER_YEAR
    young_share = 1.0 / inputs.career_years if inputs.career_years > 0.0 else 0.0
    snapshot = None
    for source in sources:
        considering = max(SWITCHING_CONSIDERATION_SHARE_PER_YEAR, idle[source])   # those who sold no hours look about
        young = min(considering, young_share)
        for is_young, share_considering in ((False, considering - young), (True, young)):
            if share_considering <= 0.0:
                continue
            own = baseline if is_young else income[source]
            kept = planned.get((source, is_young))
            if kept is not None and _plan_still_holds(kept[0], later_income, destinations):
                odds = kept[1]
            else:
                odds = _odds(inputs, state, area, source, destinations, own, later_income, vacancies, subsistence,
                             chances, is_young, income[source] if is_young else None)
                if snapshot is None:
                    snapshot = dict(later_income)
                planned[(source, is_young)] = (snapshot, odds)
            if odds is None:
                continue
            _targets, bands = odds
            rows: Dict[str, List[float]] = {}
            for band, count in enumerate(state.workers[area][source]):
                shares = bands[band]
                if count <= 0.0 or shares is None:
                    continue
                base = count * share_considering / rounds
                for trade, share in shares:
                    row = rows.get(trade)
                    if row is None:
                        row = rows[trade] = aptitude.empty_bands()
                    row[band] = base * share
            for trade, row in rows.items():
                moves.append((source, trade, row, 1.0 if is_young else _training_share(inputs, source, trade)))
    return moves


def _carry_out(state: MarketState, inputs: YearInputs, report: YearReport, area: str,
               moves: List[Move]) -> List[str]:
    """Take the switchers out of their trades and into training. Sources moving to one target on the
    same training length apply together, and the target's places are shared out between them in
    proportion to the people each sends (band by band). Returns the trades that took trainees in."""
    workers = state.workers[area]
    net: Dict[str, float] = {}
    groups: Dict[Tuple[str, float], List[Tuple[str, List[float]]]] = {}
    for source, target, bands, share in sorted(moves, key=_move_order):
        source_bands = workers[source]
        taken = list(map(min, source_bands, bands))   # `have` unless the move asks for less
        source_bands[:] = map(sub, source_bands, taken)
        groups.setdefault((target, share), []).append((source, taken))
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
    return move[1], move[0], move[3]
