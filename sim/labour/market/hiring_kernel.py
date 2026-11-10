"""The year's hiring rounds of every labour market at once, over arrays (the kernel behind `applications.hire_through_rounds`).

Markets sit end to end in the arrays, `offsets` marking where each begins; within a market the employers are in sorted id
order, so a tie in offers is broken by position. The rules are those of `applications.py`: a round dismisses a share of
each employer's hours into searching groups, caps the groups' asks at the best posted offer, ranks the posters by offer,
lets each group apply to a few of those whose offer it accepts, shares the group's hours out by the chance each employer
is the best that makes an offer, lowers the asks of the hours still searching and raises the offers of employers whose
vacancies stay open. Sums run left to right; employers paying the same offer share their tier's hours by rank order."""
import numpy as np

from sim.jit import njit


@njit
def _binomials(largest, choose):
    """`table[total, chosen]`: the ways to choose `chosen` of `total`, for totals up to `largest` and chosen up to `choose`."""
    table = np.zeros((largest + 1, choose + 1), np.int64)
    for total in range(largest + 1):
        table[total, 0] = 1
        for chosen in range(1, min(total, choose) + 1):
            table[total, chosen] = table[total - 1, chosen - 1] + table[total - 1, chosen]
    return table


@njit
def _first_below(ranked, count, offers, ask):
    """How many of the first `count` ranked posters (offers falling) offer at least `ask`."""
    low, high = 0, count
    while low < high:
        middle = (low + high) // 2
        if offers[ranked[middle]] >= ask:
            low = middle + 1
        else:
            high = middle
    return low


@njit
def _shares_of_prefix(count, ranked, offered, offers, applications, shares, ways):
    """For the first `count` ranked posters, the share of one hour of a group applying to `applications` of them at random
    that each takes on, given the chance each makes an offer; fills `shares[:count]`."""
    applied = applications if applications < count else count
    better = np.zeros(applications)
    better[0] = 1.0
    denominator = ways[count - 1, applied - 1]
    for position in range(count):
        employer = ranked[position]
        others = count - (position + 1)
        weight = 0.0
        for chosen in range(applied):
            if applied - 1 - chosen <= others:
                weight += better[chosen] * ways[others, applied - 1 - chosen]
        shares[position] = offered[employer] * applied / count * weight / denominator
        for chosen in range(applied - 1, 0, -1):
            better[chosen] = better[chosen] + better[chosen - 1] * (1.0 - offered[employer])
    start = 0
    while start < count:
        end = start + 1
        while end < count and offers[ranked[end]] == offers[ranked[start]]:
            end += 1
        tier_total = 0.0
        tier_weights = 0.0
        for position in range(start, end):
            tier_total += shares[position]
            tier_weights += offered[ranked[position]]
        for position in range(start, end):
            fraction = offered[ranked[position]] / tier_weights if tier_weights > 0.0 else 0.0
            shares[position] = 1.0 * tier_total * fraction
        start = end


@njit
def _hire_market(hired, kept, wanted, offers, pool, ask, floor, ceilings, has_ceilings, taken_amount, taken_flag,
                 rounds, applications, separation, cut, raise_share, threshold, ways):
    count_employers = hired.shape[0]
    capacity = 2 + rounds * count_employers
    group_hours = np.empty(capacity)
    group_ask = np.empty(capacity)
    group_reach = np.empty(capacity, np.int64)
    groups = 1
    group_hours[0] = pool
    group_ask[0] = ask
    paid_sum = np.empty(count_employers)
    ranked = np.empty(count_employers, np.int64)
    vacancies = np.empty(count_employers)
    applicants = np.empty(count_employers)
    offered = np.empty(count_employers)
    slot_of = np.empty(count_employers + 1, np.int64)
    slot_count = np.empty(count_employers + 1, np.int64)
    slot_hours = np.empty(count_employers + 1)
    slot_shares = np.empty((count_employers + 1, count_employers))
    slot_total = np.empty(count_employers + 1)
    keep = 1.0 - separation
    for _round in range(rounds):
        for employer in range(count_employers):
            held = hired[employer]
            if held <= 0.0:
                continue
            group_hours[groups] = held * separation
            group_ask[groups] = offers[employer]
            groups += 1
            hired[employer] = held * keep
            kept[employer] *= keep
        best = -np.inf
        posted = False
        for employer in range(count_employers):
            difference = wanted[employer] - hired[employer]
            vacancies[employer] = difference if difference > 0.0 else 0.0
            if vacancies[employer] > 0.0:
                posted = True
                if offers[employer] > best:
                    best = offers[employer]
        if posted:
            for group in range(groups):
                if best < group_ask[group]:
                    group_ask[group] = best
        poster_count = 0
        for employer in range(count_employers):
            if vacancies[employer] > 0.0:
                position = poster_count
                while position > 0 and offers[ranked[position - 1]] < offers[employer]:
                    ranked[position] = ranked[position - 1]
                    position -= 1
                ranked[position] = employer
                poster_count += 1
        for reached in range(poster_count + 1):
            slot_of[reached] = -1
        slots = 0
        for group in range(groups):
            reached = _first_below(ranked, poster_count, offers, group_ask[group])
            group_reach[group] = reached
            if slot_of[reached] < 0:
                slot_of[reached] = slots
                slot_count[slots] = reached
                slot_hours[slots] = group_hours[group]
                slots += 1
            else:
                slot_hours[slot_of[reached]] += group_hours[group]
        for position in range(poster_count):
            applicants[ranked[position]] = 0.0
        for slot in range(slots):
            reached = slot_count[slot]
            applied = applications if applications < reached else reached
            for position in range(reached):
                applicants[ranked[position]] += slot_hours[slot] * applied / reached
        for position in range(poster_count):
            employer = ranked[position]
            if applicants[employer] > 0.0:
                ratio = vacancies[employer] / applicants[employer]
                offered[employer] = ratio if ratio < 1.0 else 1.0
            else:
                offered[employer] = 0.0
        for slot in range(slots):
            reached = slot_count[slot]
            slot_total[slot] = 0.0
            if reached > 0:
                _shares_of_prefix(reached, ranked, offered, offers, applications, slot_shares[slot], ways)
                for position in range(reached):
                    slot_total[slot] += slot_shares[slot, position]
        furthest = 0
        for group in range(groups):
            furthest = max(furthest, group_reach[group])
        for position in range(furthest):        # an employer some group reaches starts its tally the first time it is reached
            employer = ranked[position]
            if not taken_flag[employer]:
                taken_flag[employer] = True
                taken_amount[employer] = 0.0
                paid_sum[employer] = 0.0
        for group in range(groups):
            slot = slot_of[group_reach[group]]
            hours_of_group = group_hours[group]
            for position in range(slot_count[slot]):
                employer = ranked[position]
                amount = hours_of_group * slot_shares[slot, position]
                hired[employer] += amount
                taken_amount[employer] += amount
                paid_sum[employer] += amount * offers[employer]
            group_hours[group] = hours_of_group - hours_of_group * slot_total[slot]
        survivors = 0
        for group in range(groups):
            if group_hours[group] > 1e-9:
                current = group_ask[group]
                lowered = current * (1.0 - cut)
                floored = floor if floor < current else current
                group_hours[survivors] = group_hours[group]
                group_ask[survivors] = floored if floored > lowered else lowered
                survivors += 1
        groups = survivors
        if has_ceilings:
            for employer in range(count_employers):
                offer = offers[employer]
                if wanted[employer] <= 0.0 or (wanted[employer] - hired[employer]) / wanted[employer] <= threshold:
                    continue
                raised = offer * (1.0 + raise_share)
                if ceilings[employer] < raised:
                    raised = ceilings[employer]
                if raised > offer:
                    offers[employer] = raised
    for employer in range(count_employers):
        if taken_flag[employer] and taken_amount[employer] > 0.0:
            offers[employer] = paid_sum[employer] / taken_amount[employer]


@njit
def hire_markets(offsets, hired, kept, wanted, offers, ceilings, pools, asks, floors, has_ceilings, taken_amount, taken_flag,
                 rounds, applications, separation, cut, raise_share, threshold):
    """Run the rounds of each market (employers `offsets[i]:offsets[i + 1]`); `hired`, `kept` and `offers` change in place,
    `taken_amount` and `taken_flag` say what each employer took on."""
    largest = 0
    for market in range(offsets.shape[0] - 1):
        largest = max(largest, offsets[market + 1] - offsets[market])
    ways = _binomials(largest, applications)
    for market in range(offsets.shape[0] - 1):
        low = offsets[market]
        high = offsets[market + 1]
        _hire_market(hired[low:high], kept[low:high], wanted[low:high], offers[low:high], pools[market], asks[market],
                     floors[market], ceilings[low:high], has_ceilings[market], taken_amount[low:high],
                     taken_flag[low:high], rounds, applications, separation, cut, raise_share, threshold, ways)
