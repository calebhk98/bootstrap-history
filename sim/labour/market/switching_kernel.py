"""The choice odds of workers weighing a change of trade, for every ability band at once (the kernel behind
`switching._odds`).

A band scores each target trade by its chance of finishing the training times the gain, less the cost of the training;
an established worker considers only targets scoring above staying, the young consider all. Scores become logit weights
against staying; targets under a negligible share of the total are dropped and their weight goes to the leading target.
Sums run left to right."""
import numpy as np

from sim.jit import njit

from .switching_discounts import FULL, RETRAINED, YOUNG, annuity, career_gain


@njit
def band_shares(scores, picked, count, stay_score, young, scale, negligible, shares, moves, weights):
    """The choice odds of the bands over `count` targets. `scores[band, slot]` is the score of the target in `picked[slot]` (its
    column in `shares`), in units of the area's subsistence (`stay_score` is already in them). Fills `shares[band, picked[slot]]`
    (the caller has zeroed them: a target not picked or dropped stays zero) and `moves[band]`, whether the band moves at all
    (the caller has cleared it). `weights` is a work array `count` long."""
    for band in range(scores.shape[0]):
        picked_count = 0
        top = stay_score
        for slot in range(count):
            score = scores[band, slot]
            if score > 0.0 or young:
                picked_count += 1
                if score > top:
                    top = score
        if picked_count == 0:
            continue
        total = 0.0
        heaviest = -1.0
        leader = -1
        for slot in range(count):
            score = scores[band, slot]
            if score > 0.0 or young:
                weights[slot] = np.exp((score - top) / scale) if scale != 1.0 else np.exp(score - top)
                total += weights[slot]
                if weights[slot] > heaviest:
                    heaviest = weights[slot]
                    leader = slot
            else:
                weights[slot] = -1.0
        total += np.exp((stay_score - top) / scale) if scale != 1.0 else np.exp(stay_score - top)
        cutoff = total * negligible
        dropped = 0.0
        for slot in range(count):
            if weights[slot] >= 0.0:
                if weights[slot] >= cutoff:
                    shares[band, picked[slot]] = weights[slot] / total
                else:
                    dropped += weights[slot]
        shares[band, picked[leader]] += dropped / total
        if shares[band, picked[leader]] < negligible:
            for slot in range(count):
                shares[band, picked[slot]] = 0.0
            continue
        moves[band] = True


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
def _career_scores(chances, gain, lost, unit, destination, scores, slot):
    """The bands' scores for the destination, in units of `unit`, put in column `slot` of `scores`."""
    for band in range(scores.shape[0]):
        scores[band, slot] = (chances[destination, band] * gain - lost) / unit


@njit
def plan_area(counts, income, idle, baseline, later, vacancies, chances, discounts, retrained, source_position,
              source_is_fallback, fallback_position, subsistence, rate, career_years, consideration_floor, remaining_share,
              plan_tolerance, taste, negligible, planned_valid, planned_then, planned_targets, planned_shares, planned_moves,
              active, considering):
    """The choice odds of every (source trade, young or established) group of an area for one round of switching
    (`switching._planned_moves`). A group keeps the odds it planned on while no destination's income after training has
    moved past the tolerance; otherwise they are worked out afresh and kept. `planned_*` carry the odds from round to round:
    `planned_shares[source, young, band, destination]` and `planned_moves[source, young, band]` are the answer to read.
    `active[source, young]` is whether the group weighs a switch at all, `considering` the share of the source's people who do.
    `discounts` are the year's tables (`switching_discounts.discount_tables`); `retrained[source, destination]` says a
    source's established workers train a share of the destination's years."""
    count_sources = counts.shape[0]
    count_bands = counts.shape[1]
    count_destinations = later.shape[0]
    tolerance = plan_tolerance * subsistence
    young_share = 1.0 / career_years if career_years > 0.0 else 0.0
    picked = np.empty(count_destinations, np.int64)
    scores_room, weights_room = np.empty((count_bands, count_destinations)), np.empty(count_destinations)
    stay_start, stay_after = np.exp(-max(0.0, rate) * 0.0), annuity(rate, career_years - 0.0)
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
            for slot in range(count):
                destination = picked[slot]
                planned_targets[source, young_flag, destination] = True
                kind = YOUNG if young else (RETRAINED if retrained[source, destination] else FULL)
                gain = career_gain(later[destination] - own, discounts.start[kind, destination], discounts.after[kind, destination],
                                   discounts.pays[kind, destination])
                _career_scores(chances, gain, own * discounts.lost[kind, destination], subsistence, destination, scores_room, slot)
            stay_score = 0.0
            if young:
                stay_score = career_gain(income[source] - own, stay_start, stay_after, career_years > 0.0) / subsistence
            band_shares(scores_room, picked, count, stay_score, young, taste, negligible, planned_shares[source, young_flag],
                        planned_moves[source, young_flag], weights_room)


@njit
def _live_groups(counts, active, moving, live_source, live_young):
    """The groups that can move anyone (active, with a band that moves and has people), by source then established before young."""
    live = 0
    for source in range(counts.shape[0]):
        for young in range(2):
            if not active[source, young]:
                continue
            for band in range(counts.shape[1]):
                if moving[source, young, band] and counts[source, band] > 0.0:
                    live_source[live], live_young[live] = source, young
                    live += 1
                    break
    return live


@njit
def collect_moves(counts, considering, active, moving, planned_targets, planned_shares, training_share, rounds, moves_source,
                  moves_destination, moves_share, moves_rows):
    """The round's moves in the order they are carried out (by destination, then source, then the established workers before
    the young; the established share of the training years is never above the young's one): a row for each (source,
    young, destination) where some band of an active source with people sends people there. Fills the move arrays (as long as
    every possible move) and returns how many moves there are."""
    count_sources, count_bands, count_destinations = counts.shape[0], counts.shape[1], training_share.shape[1]
    live_source, live_young = np.empty(2 * count_sources, np.int64), np.empty(2 * count_sources, np.int64)
    live = _live_groups(counts, active, moving, live_source, live_young)
    found = 0
    for destination in range(count_destinations):
        for group in range(live):
            source, young = live_source[group], live_young[group]
            if not planned_targets[source, young, destination]:
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
def group_moves(destinations, shares, group_of, members, group_starts):
    """Group the moves by (destination, share of the training years), groups numbered in the order their first move comes.
    Fills `group_of[move]`, `members` (the moves of each group in carrying-out order, group after group) and
    `group_starts` (length groups + 1); returns the number of groups."""
    count = destinations.shape[0]
    first = np.empty(count, np.int64)
    highest = 0
    for move in range(count):
        highest = max(highest, destinations[move])
    newest = np.full(highest + 1, -1, np.int64)      # per destination: its latest group (it has few: one per training length)
    older = np.empty(count, np.int64)                            # per group: the group of the same destination made before it
    groups = 0
    for move in range(count):
        found = newest[destinations[move]]
        while found >= 0 and shares[first[found]] != shares[move]:
            found = older[found]
        if found < 0:
            first[groups] = move
            older[groups] = newest[destinations[move]]
            newest[destinations[move]] = groups
            found = groups
            groups += 1
        group_of[move] = found
    group_starts[0] = 0
    for group in range(groups):
        group_starts[group + 1] = 0
    for move in range(count):
        group_starts[group_of[move] + 1] += 1
    for group in range(groups):
        group_starts[group + 1] += group_starts[group]
    filled = np.zeros(groups, np.int64)
    for move in range(count):
        group = group_of[move]
        members[group_starts[group] + filled[group]] = move
        filled[group] += 1
    return groups


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
