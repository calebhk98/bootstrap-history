"""The respend rounds' settled pairs summed per good in one kernel call: for each good that traded, what each agent paid and received
and what each (holder, tile) gave and took, as the arguments of `book_settled.post_settled_by_numbers`
(`goods_respend_unpack.write_settlement` did about thirteen numpy calls and filled a dict per good).

Sums are added in the order the pairs are given, as `numpy.bincount` adds them. Agents come out ascending by their place in the
packed agents; a good's holders come seller keys first (ascending key number), then buyer rows (ascending), a (holder, tile) that is
both merged at its first place."""
import numpy

from sim.jit import njit


@njit
def settlement_by_good(item, buyer_agent, seller_agent, buyer_row, offer_key, units, money, agent_number, key_holder, key_tile,
                       buyer_holder, buyer_tile, good_count):
    """(goods, people_ptr, people, paid, received, move_ptr, holder, tile, given, taken) for the goods that have a pair, ascending.

    A pair is `item` (the good's place), the packed agent index of its buyer and seller, the buyer's row, the key number of the offer,
    the units moved and the money paid. `agent_number` gives each packed agent's number on the book, `key_holder` and `key_tile` the book
    numbers of each offer key's holder and tile, `buyer_holder` and `buyer_tile` those of each buyer row. For a good, `people[people_ptr[i]:
    people_ptr[i + 1]]` are the book numbers of the agents that bought or sold, with what each `paid` and `received`; `holder`, `tile`, `given`
    and `taken` are the (holder, tile) entries cut by `move_ptr`."""
    pairs = len(item)
    agents = len(agent_number)
    keys = len(key_holder)
    buyers = len(buyer_holder)
    per_good = numpy.zeros(good_count + 1, dtype=numpy.int64)
    for pair in range(pairs):
        per_good[item[pair] + 1] += 1
    for good in range(good_count):
        per_good[good + 1] += per_good[good]
    cursor = per_good[:good_count].copy()
    order = numpy.empty(pairs, dtype=numpy.int64)
    for pair in range(pairs):
        order[cursor[item[pair]]] = pair
        cursor[item[pair]] += 1
    present_goods = 0
    for good in range(good_count):
        if per_good[good + 1] > per_good[good]:
            present_goods += 1
    goods = numpy.empty(present_goods, dtype=numpy.int64)
    people_ptr = numpy.zeros(present_goods + 1, dtype=numpy.int64)
    move_ptr = numpy.zeros(present_goods + 1, dtype=numpy.int64)
    room_people, room_moves = agents * present_goods, (keys + buyers) * present_goods
    all_people = numpy.empty(room_people, dtype=numpy.int64)
    all_paid = numpy.empty(room_people)
    all_received = numpy.empty(room_people)
    all_holder = numpy.empty(room_moves, dtype=numpy.int64)
    all_tile = numpy.empty(room_moves, dtype=numpy.int64)
    all_given = numpy.empty(room_moves)
    all_taken = numpy.empty(room_moves)
    paid = numpy.zeros(agents)
    received = numpy.zeros(agents)
    seen_agent = numpy.zeros(agents, dtype=numpy.bool_)
    given_key = numpy.zeros(keys)
    seen_key = numpy.zeros(keys, dtype=numpy.bool_)
    taken_row = numpy.zeros(buyers)
    seen_row = numpy.zeros(buyers, dtype=numpy.bool_)
    found = 0
    for good in range(good_count):
        first, last = per_good[good], per_good[good + 1]
        if last == first:
            continue
        for place in range(first, last):
            pair = order[place]
            paid[buyer_agent[pair]] += money[pair]
            received[seller_agent[pair]] += money[pair]
            seen_agent[buyer_agent[pair]] = True
            seen_agent[seller_agent[pair]] = True
            given_key[offer_key[pair]] += units[pair]
            seen_key[offer_key[pair]] = True
            taken_row[buyer_row[pair]] += units[pair]
            seen_row[buyer_row[pair]] = True
        at = people_ptr[found]
        for agent in range(agents):
            if seen_agent[agent]:
                all_people[at] = agent_number[agent]
                all_paid[at] = paid[agent]
                all_received[at] = received[agent]
                at += 1
                paid[agent] = 0.0
                received[agent] = 0.0
                seen_agent[agent] = False
        people_ptr[found + 1] = at
        start = move_ptr[found]
        at = start
        for key in range(keys):                  # seller keys first: the (holder, tile) of a key is its own entry
            if seen_key[key]:
                all_holder[at] = key_holder[key]
                all_tile[at] = key_tile[key]
                all_given[at] = given_key[key]
                all_taken[at] = 0.0
                at += 1
                given_key[key] = 0.0
                seen_key[key] = False
        for row in range(buyers):                # then buyer rows, merged into the entry of the same (holder, tile)
            if seen_row[row]:
                entry = -1
                for earlier in range(start, at):
                    if all_holder[earlier] == buyer_holder[row] and all_tile[earlier] == buyer_tile[row]:
                        entry = earlier
                        break
                if entry < 0:
                    entry = at
                    all_holder[at] = buyer_holder[row]
                    all_tile[at] = buyer_tile[row]
                    all_given[at] = 0.0
                    all_taken[at] = 0.0
                    at += 1
                all_taken[entry] += taken_row[row]
                taken_row[row] = 0.0
                seen_row[row] = False
        move_ptr[found + 1] = at
        goods[found] = good
        found += 1
    return (goods, people_ptr, all_people[:people_ptr[present_goods]].copy(), all_paid[:people_ptr[present_goods]].copy(),
            all_received[:people_ptr[present_goods]].copy(), move_ptr, all_holder[:move_ptr[present_goods]].copy(),
            all_tile[:move_ptr[present_goods]].copy(), all_given[:move_ptr[present_goods]].copy(),
            all_taken[:move_ptr[present_goods]].copy())
