"""The plain Python rules of switching's choice odds and planned moves, as they ran before the arrays kernel
(`switching_kernel.plan_area`): kept so a test runs both on the same inputs. Not used by the game."""
from typing import Dict, List, Mapping, Tuple

import numpy as np

from sim.labour.market import aptitude, expectations, switching_kernel
from sim.labour.market.premium import annuity_factor
from sim.labour.market.switching import (NEGLIGIBLE_MOVE_SHARE, PLAN_REUSE_TOLERANCE, REMAINING_CAREER_SHARE,
                                         SWITCHING_CONSIDERATION_SHARE_PER_YEAR, SWITCHING_TASTE_SCALE, Move,
                                         RETRAINING_SHARE_WITHIN_FAMILY)
from sim.labour.market.records import YearInputs
from sim.labour.market.trades import fallback_trade


def _training_share(inputs: YearInputs, source: str, target: str) -> float:
    same_family = inputs.trades[source].family == inputs.trades[target].family
    return RETRAINING_SHARE_WITHIN_FAMILY if same_family else 1.0


def _odds(inputs, state, area, source, destinations, own, later_income, vacancies, subsistence, chances, young,
          stay_income=None):
    """The odds of each band of `source` workers moving to each worthwhile destination: (targets, per
    band the share of each target), or None for a band that stays. `own` is the income given up. The young weigh a
    whole career and weigh every trade paying more than `own` after training, even one worth less than staying
    once the training is paid for (module docstring), and the unskilled trade too where their own pays less than it. The young may stay in `source`, scored at `stay_income` (what it
    pays now) over the career against `own`; an established worker's stay scores nothing, being the income given up."""
    rate = inputs.discount_rate
    remaining = inputs.career_years if young else inputs.career_years * REMAINING_CAREER_SHARE
    if young:   # a vacancy that pays no more than the unskilled option is not an opening (it is in `later_income`)
        margin = PLAN_REUSE_TOLERANCE * subsistence
        fallback = fallback_trade(inputs.trades)
        leaves_for_unskilled = stay_income is not None and stay_income < own and fallback != source   # their trade pays less than unskilled work
        targets = [trade for trade in destinations if trade != source
                   and (later_income[trade] > own + margin or (leaves_for_unskilled and trade == fallback))]
    else:
        targets = [trade for trade in destinations if trade != source and (later_income[trade] > own or trade in vacancies)]
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
    shares = np.empty((len(state.workers[area][source]), len(targets)))
    moves = switching_kernel.band_shares(np.array([chances[trade] for trade in targets]), np.array(gain), np.array(lost),
                                         subsistence, stay_score, young, SWITCHING_TASTE_SCALE, NEGLIGIBLE_MOVE_SHARE, shares)
    bands = [[(trade, share) for trade, share in zip(targets, row) if share > 0.0] if moving else None
             for row, moving in zip(shares.tolist(), moves.tolist())]
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


def _planned_moves(state, inputs, area, sources, destinations, income, baseline, later_income, vacancies,
                   subsistence, chances, planned, idle) -> List[Move]:
    moves: List[Move] = []
    rounds = expectations.DECISION_ROUNDS_PER_YEAR
    tolerance = PLAN_REUSE_TOLERANCE * subsistence
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
            if kept is not None and _plan_still_holds(kept[0], later_income, own, kept[1], vacancies,
                                                      destinations, tolerance):
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
