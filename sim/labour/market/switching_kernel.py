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
def collect_moves(counts, considering, active, moving, planned_shares, training_share, rounds, moves_source, moves_destination,
                  moves_share, moves_rows):
    """The round's moves in the order they are carried out (by destination, then source, then the established workers before
    the young; the established share of the training years is never above the young's one): a row for each (source,
    young, destination) where some band of an active source with people sends people there. Fills the move arrays (as long as
    every possible move) and returns how many moves there are."""
    count_sources, count_bands, count_destinations = counts.shape[0], counts.shape[1], training_share.shape[1]
    found = 0
    for destination in range(count_destinations):
        for source in range(count_sources):
            for young in range(2):
                if not active[source, young]:
                    continue
                picked = False
                for band in range(count_bands):
                    if moving[source, young, band] and counts[source, band] > 0.0 and planned_shares[source, young, band, destination] > 0.0:
                        picked = True
                        moves_rows[found, band] = counts[source, band] * considering[source, young] / rounds * planned_shares[source, young, band, destination]
                    else:
                        moves_rows[found, band] = 0.0
                if picked:
                    moves_source[found] = source
                    moves_destination[found] = destination
                    moves_share[found] = 1.0 if young == 1 else training_share[source, destination]
                    found += 1
    return found


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


@njit
def _incumbents(have, source_of_destination, added, destination):
    """The people working a destination trade now: its row among the sources, and what direct entry has added."""
    total = 0.0
    row = source_of_destination[destination]
    if row >= 0:
        for band in range(have.shape[1]):
            total += have[row, band]
    for band in range(added.shape[1]):
        total += added[destination, band]
    return total


@njit
def enrol_groups(group_starts, members, group_destination, group_share, taken, move_source, have, source_of_destination, added,
                 years_of_destination, apprentices_per_master, seats, school_bonus, enrolled, last_years, last_bonus, last_exists,
                 admitted, kind, years, bonus, moved, changed):
    """`training.enrol` for each group of moves, in order, with the refusals handed back to the senders (`switching._carry_out`).
    Moves of one group are those `members[group_starts[g]:group_starts[g + 1]]` (rows of `taken[move, band]`), going to one
    destination on one share of the training years. `have[source, band]` holds the people left at work and takes the refusals
    back; direct entry (a trade needing no training) goes to the destination's row among the sources
    (`source_of_destination`, -1 where it is not one) or to `added`. `enrolled`, `last_years`, `last_bonus` and `last_exists` stand
    for the destinations' cohorts and change as groups enrol. Per group: `admitted[g]` the people admitted per band, `kind[g]` 0
    nothing enrolled, 1 a new cohort, 2 added to the last cohort, 3 direct entry, with its `years` and `bonus`; per move `moved`
    the people it sends net of those turned back; `changed[source]` marks the rows of `have` that moved."""
    count_bands = taken.shape[1]
    combined = np.empty(count_bands)
    refused = np.empty(count_bands)
    for group in range(group_starts.shape[0] - 1):
        low = group_starts[group]
        high = group_starts[group + 1]
        destination = group_destination[group]
        for band in range(count_bands):
            total = 0.0
            for member in range(low, high):
                total += taken[members[member], band]
            combined[band] = total
            refused[band] = 0.0
            admitted[group, band] = 0.0
        for member in range(low, high):
            moved[members[member]] = 0.0
            for band in range(count_bands):
                moved[members[member]] += taken[members[member], band]
        kind[group] = 0
        wanting = 0.0
        for band in range(count_bands):
            wanting += combined[band]
        share = group_share[group] if group_share[group] > 0.0 else 0.0
        group_years = years_of_destination[destination] * share
        years[group] = group_years
        bonus[group] = 0.0
        if wanting <= 0.0:
            for band in range(count_bands):
                refused[band] = combined[band]
        elif group_years <= 0.0:
            kind[group] = 3
            row = source_of_destination[destination]
            for band in range(count_bands):
                if row >= 0:
                    have[row, band] += combined[band]
                    changed[row] = True
                else:
                    added[destination, band] += combined[band]
        else:
            capacity = seats[destination] + _incumbents(have, source_of_destination, added, destination) * apprentices_per_master
            room = capacity - enrolled[destination]
            share_admitted = room / wanting if room > 0.0 else 0.0
            if share_admitted > 1.0:
                share_admitted = 1.0
            if share_admitted <= 0.0:
                for band in range(count_bands):
                    refused[band] = combined[band]
            else:
                group_bonus = school_bonus[destination] * (seats[destination] / capacity) if capacity > 0.0 else 0.0
                total_admitted = 0.0
                for band in range(count_bands):
                    if share_admitted >= 1.0:
                        admitted[group, band] = combined[band]
                    else:
                        admitted[group, band] = combined[band] * share_admitted
                        refused[band] = combined[band] - admitted[group, band]
                    total_admitted += admitted[group, band]
                enrolled[destination] += total_admitted
                bonus[group] = group_bonus
                if last_exists[destination] and last_years[destination] == group_years and last_bonus[destination] == group_bonus:
                    kind[group] = 2
                else:
                    kind[group] = 1
                    last_exists[destination] = True
                    last_years[destination] = group_years
                    last_bonus[destination] = group_bonus
        anything = False
        for band in range(count_bands):
            if refused[band] != 0.0:
                anything = True
        if anything:
            for member in range(low, high):
                move = members[member]
                row = move_source[move]
                for band in range(count_bands):
                    if high - low == 1:
                        back = refused[band]
                    elif combined[band] > 0.0:
                        back = refused[band] * taken[move, band] / combined[band]
                    else:
                        back = 0.0
                    have[row, band] += back
                    moved[move] -= back
                changed[row] = True
