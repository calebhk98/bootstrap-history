"""The per-good loop of `goods_respend_unpack.write_settlement` as it was (a handful of numpy calls and a dict per good), kept so
`goods_respend_settle_kernel.settlement_by_good` is tested against it. Returns, per good that has a pair, the arguments of
`post_settled_by_numbers`: (good, people, paid, received, holders, tiles, given, taken)."""
import numpy

from sim.economy.goods_respend_unpack import paid_and_received, summed


def plain_settlement_by_good(item, buyer_agent, seller_agent, buyer_row, offer_key, units, money, agent_number, key_holder, key_tile,
                             buyer_holder, buyer_tile):
    found = []
    for good in numpy.unique(item).tolist():
        mine = item == good
        people, paid, received = paid_and_received(buyer_agent[mine], seller_agent[mine], money[mine], len(agent_number))
        moves = {}
        seller_keys, given = summed(offer_key[mine], units[mine])
        for key, amount in zip(seller_keys.tolist(), given.tolist()):
            moves.setdefault((int(key_holder[key]), int(key_tile[key])), [0.0, 0.0])[0] += amount
        rows, taken = summed(buyer_row[mine], units[mine])
        for row, amount in zip(rows.tolist(), taken.tolist()):
            moves.setdefault((int(buyer_holder[row]), int(buyer_tile[row])), [0.0, 0.0])[1] += amount
        found.append((good, agent_number[people], paid, received, [each[0] for each in moves], [each[1] for each in moves],
                      [each[0] for each in moves.values()], [each[1] for each in moves.values()]))
    return found


def plain_flatten_baskets(baskets, good_index) -> tuple:
    """`goods_respend_pack.flatten_baskets` as it was: the triple loop over baskets, needs and goods."""
    from sim.economy.goods_respend import need_of_good
    need_ids = sorted({spec.need_id for basket in baskets for spec in basket.needs})
    slot_of = {need_id: slot for slot, need_id in enumerate(need_ids)}
    need_ptr, weight, slots, has_limits, good_ptr = [0], [], [], [], [0]
    good_rows, effects, limits, limited = [], [], [], []
    for basket in baskets:
        for spec in basket.needs:
            weight.append(spec.budget_weight)
            slots.append(slot_of[spec.need_id])
            has_limits.append(bool(spec.share_limits))
            share_limits = dict(spec.share_limits)
            for good, effect in spec.goods:
                good_rows.append(good_index[good])
                effects.append(effect)
                limited.append(good in share_limits)
                limits.append(share_limits.get(good, 0.0))
            good_ptr.append(len(good_rows))
        need_ptr.append(len(weight))
    need_of_good_slot = numpy.full((len(baskets), len(good_index)), -1, dtype=numpy.int64)
    for index, basket in enumerate(baskets):
        for good, need_id in need_of_good(basket).items():
            need_of_good_slot[index, good_index[good]] = slot_of[need_id]
    return (numpy.array(need_ptr, dtype=numpy.int64), numpy.array(weight, dtype=float), numpy.array(slots, dtype=numpy.int64),
            numpy.array(has_limits, dtype=numpy.bool_), numpy.array(good_ptr, dtype=numpy.int64),
            numpy.array(good_rows, dtype=numpy.int64), numpy.array(effects, dtype=float), numpy.array(limits, dtype=float),
            numpy.array(limited, dtype=numpy.bool_), numpy.array([1.0 - basket.substitution for basket in baskets]),
            numpy.array([basket.substitution for basket in baskets]), need_of_good_slot, len(need_ids))
