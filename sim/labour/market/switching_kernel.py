"""The choice odds of workers weighing a change of trade, for every ability band at once (the kernel behind
`switching._odds`).

A band scores each target trade by its chance of finishing the training times the gain, less the cost of the training;
an established worker considers only targets scoring above staying, the young consider all. Scores become logit weights
against staying; targets under a negligible share of the total are dropped and their weight goes to the leading target.
Sums run left to right."""
import numpy as np

from sim.jit import njit


@njit
def band_shares(chances, gain, lost, unit, stay_score, young, scale, negligible, shares):
    """Fill `shares[band, target]` (zero where a target is not picked or is dropped) and return, per band, whether the band
    moves at all. `chances[target, band]` is the chance of finishing, `gain` and `lost` are per target, scores are in units of `unit`
    (`stay_score` is already in them)."""
    count_targets = chances.shape[0]
    count_bands = chances.shape[1]
    moves = np.zeros(count_bands, np.bool_)
    scores = np.empty(count_targets)
    weights = np.empty(count_targets)
    for band in range(count_bands):
        picked = 0
        top = stay_score
        for target in range(count_targets):
            shares[band, target] = 0.0
            score = (chances[target, band] * gain[target] - lost[target]) / unit
            scores[target] = score
            if score > 0.0 or young:
                picked += 1
                if score > top:
                    top = score
        if picked == 0:
            continue
        total = 0.0
        heaviest = -1.0
        leader = -1
        for target in range(count_targets):
            if scores[target] > 0.0 or young:
                weights[target] = np.exp((scores[target] - top) / scale)
                total += weights[target]
                if weights[target] > heaviest:
                    heaviest = weights[target]
                    leader = target
            else:
                weights[target] = -1.0
        total += np.exp((stay_score - top) / scale)
        cutoff = total * negligible
        dropped = 0.0
        for target in range(count_targets):
            if weights[target] >= 0.0:
                if weights[target] >= cutoff:
                    shares[band, target] = weights[target] / total
                else:
                    dropped += weights[target]
        shares[band, leader] += dropped / total
        if shares[band, leader] < negligible:
            for target in range(count_targets):
                shares[band, target] = 0.0
            continue
        moves[band] = True
    return moves


@njit
def _annuity(rate, years):
    """`premium.annuity_factor`."""
    if years <= 0.0:
        return 0.0
    if rate <= 0.0:
        return years
    return (1.0 - np.exp(-rate * years)) / rate


@njit
def _present_value(income, rate, start, until):
    """`expectations.present_value`."""
    if until <= start:
        return 0.0
    return income * np.exp(-max(0.0, rate) * start) * _annuity(rate, until - start)


@njit
def _plan_holds(then, later, own, targets, vacancies, tolerance):
    """`switching._plan_still_holds`: no destination's income after training has moved enough to change the odds."""
    for destination in range(later.shape[0]):
        if abs(later[destination] - then[destination]) <= tolerance:
            continue
        if targets[destination] or later[destination] > own or vacancies[destination]:
            return False
    return True


@njit
def plan_area(counts, income, idle, baseline, later, vacancies, chances, years, training_share, source_position,
              source_is_fallback, fallback_position, subsistence, rate, career_years, consideration_floor, remaining_share,
              plan_tolerance, taste, negligible, planned_valid, planned_then, planned_targets, planned_shares, planned_moves,
              active, considering):
    """The choice odds of every (source trade, young or established) group of an area for one round of switching
    (`switching._planned_moves`). A group keeps the odds it planned on while no destination's income after training has
    moved past the tolerance; otherwise they are worked out afresh and kept. `planned_*` carry the odds from round to round:
    `planned_shares[source, young, band, destination]` and `planned_moves[source, young, band]` are the answer to read.
    `active[source, young]` is whether the group weighs a switch at all, `considering` the share of the source's people who do."""
    count_sources = counts.shape[0]
    count_bands = counts.shape[1]
    count_destinations = later.shape[0]
    tolerance = plan_tolerance * subsistence
    young_share = 1.0 / career_years if career_years > 0.0 else 0.0
    picked = np.empty(count_destinations, np.int64)
    for source in range(count_sources):
        weighing = max(consideration_floor, idle[source])
        young_part = min(weighing, young_share)
        for young_flag in range(2):
            share = weighing - young_part if young_flag == 0 else young_part
            active[source, young_flag] = share > 0.0
            considering[source, young_flag] = share
            if share <= 0.0:
                continue
            young = young_flag == 1
            own = baseline if young else income[source]
            if planned_valid[source, young_flag] and _plan_holds(planned_then[source, young_flag], later, own,
                                                                 planned_targets[source, young_flag], vacancies, tolerance):
                continue
            planned_valid[source, young_flag] = True
            planned_then[source, young_flag, :] = later
            planned_targets[source, young_flag, :] = False
            planned_moves[source, young_flag, :] = False
            planned_shares[source, young_flag, :, :] = 0.0
            remaining = career_years if young else career_years * remaining_share
            count = 0
            leaves_for_unskilled = young and income[source] < own and not source_is_fallback[source]
            for destination in range(count_destinations):
                if destination == source_position[source]:
                    continue
                if young:
                    worthwhile = later[destination] > own + plan_tolerance * subsistence or (
                        leaves_for_unskilled and destination == fallback_position)
                else:
                    worthwhile = later[destination] > own or vacancies[destination]
                if worthwhile:
                    picked[count] = destination
                    count += 1
            if count == 0:
                continue
            gain = np.empty(count)
            lost = np.empty(count)
            chance = np.empty((count, count_bands))
            for slot in range(count):
                destination = picked[slot]
                trained = years[destination] * (1.0 if young else training_share[source, destination])
                lost[slot] = own * _annuity(rate, trained)
                gain[slot] = _present_value(later[destination] - own, rate, trained, remaining)
                chance[slot, :] = chances[destination, :]
                planned_targets[source, young_flag, destination] = True
            stay_score = 0.0
            if young:
                stay_score = _present_value(income[source] - own, rate, 0.0, remaining) / subsistence
            shares = np.empty((count_bands, count))
            moves = band_shares(chance, gain, lost, subsistence, stay_score, young, taste, negligible, shares)
            for band in range(count_bands):
                planned_moves[source, young_flag, band] = moves[band]
                for slot in range(count):
                    planned_shares[source, young_flag, band, picked[slot]] = shares[band, slot]


@njit
def take_moves(sources, rows, have, taken):
    """Carry out the moves in order: each takes from its source's bands what it asks for, no more than the source has left
    (`have[source, band]` is updated). Fills `taken[move, band]`."""
    for move in range(sources.shape[0]):
        for band in range(have.shape[1]):
            amount = rows[move, band]
            left = have[sources[move], band]
            if left < amount:
                amount = left
            taken[move, band] = amount
            have[sources[move], band] = left - amount
