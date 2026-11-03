"""Workers re-weigh their trade against the others, with a stay option (DESIGN.md, step 4).

A switcher becomes a trainee of the new trade (shorter within a skill family) through the same places
as any trainee; those not admitted stay in their old trade. The fallback trade takes people straight in.

Of the people who consider a change in a year, one career's worth in a lifetime of them (`1 / career_years` of
a trade's people) are the young who have just come of working age: they hold no trade yet, so their baseline is the
unskilled income, their horizon is a whole career and they weigh a trade with no stay threshold, since the training
premium (premium.py) leaves exactly such a person indifferent at the long-run wage. Their own trade is one of their
options, scored at what it pays now over a career against the unskilled income with no training to pay, so a trade that
pays best keeps its young. The rest are established workers:
half a career ahead, the old trade's income to give up, and only a move worth more than staying. The economy keeps
the core's people equal to demography's by scaling every worker and trainee of a tile by one factor
(`scale_people` in sim/economy/labour_state.py), so trainees in a cohort are not lost or created by it.
"""
import math
from operator import sub
from typing import Dict, List, Mapping, Tuple

from sim.constants import declare

from . import aptitude, expectations, training
from .premium import annuity_factor
from .records import MarketState, YearInputs, YearReport
from .trades import fallback_trade

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

Move = Tuple[str, str, List[float], float]   # source trade, destination trade, people per band, share of the training years


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
    fallback = fallback_trade(inputs.trades)
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
        idle = {trade: expectations.idle_share_of(clearings.get((area, trade))) for trade in sources}
        baseline = expectations.expected_income(state, inputs, clearings, area, fallback)   # the young's unskilled option
        vacancies = {trade for trade in destinations
                     if (area, trade) in clearings and clearings[(area, trade)].vacant_hours > 0.0}
        # a switcher trains first, so a destination is weighed by its income after training (capped at the long-run
        # training cost), not by today's scarcity wage; a source is weighed by what it pays today (Complaint 678)
        later_income: Dict[str, float] = {}
        planned: Dict[Tuple[str, bool], tuple] = {}   # (source, young) -> (later income it was planned on, odds of each target per band)
        stale = destinations   # trades whose income after training must be re-read (enrolling changes it)
        for _round in range(rounds):
            for trade in stale:
                later_income[trade] = expectations.income_at_graduation(state, inputs, clearings, area, trade,
                                                                        chances[trade])
            moves = _planned_moves(state, inputs, area, sources, destinations, income, baseline, later_income, vacancies,
                                   subsistence, chances, planned, idle)
            stale = _carry_out(state, inputs, report, area, moves)


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
    bands = []
    exp = math.exp
    for band, count in enumerate(state.workers[area][source]):
        scores = []
        picked = []
        for index, trade in enumerate(targets):
            score = (chances[trade][band] * gain[index] - lost[index]) / subsistence
            if score > 0.0 or young:   # an established worker does not consider a move worth less than staying
                scores.append(score)
                picked.append(index)
        if not scores:
            bands.append(None)
            continue
        top = max(scores + [stay_score])
        scale = SWITCHING_TASTE_SCALE
        weights = [exp((score - top) / scale) for score in scores]
        total = math.fsum(weights + [exp((stay_score - top) / scale)])   # the last is staying
        cutoff = total * NEGLIGIBLE_MOVE_SHARE
        leader = weights.index(max(weights))
        shares = [weight / total if weight >= cutoff else 0.0 for weight in weights]
        shares[leader] += math.fsum(weight for weight in weights if weight < cutoff) / total
        if shares[leader] < NEGLIGIBLE_MOVE_SHARE:   # every destination is far worse than staying
            bands.append(None)
            continue
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
