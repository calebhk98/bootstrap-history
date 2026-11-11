"""The room a merchant has to bid for, one route at a time over dicts: `merchants_shares.room_left`, the rule the compiled
`merchants_book_kernel.room_of` and `rooms_of` follow."""
import math

from sim.economy import merchants_shares


def plain_rooms(destinations, sources, volumes, held, group_into, group_out, own_share):
    """`room_left` for each (destination slot, source slot) pair; a slot is the area `a<slot>` of one good, NaN a volume never seen."""
    def known(slot):
        return None if math.isnan(volumes[slot]) else float(volumes[slot])
    expected = {("g", "a%d" % slot): known(slot) for slot in range(len(volumes)) if known(slot) is not None}
    group = merchants_shares.RouteShares()
    group.into = {("g", "a%d" % slot): float(group_into[slot]) for slot in range(len(volumes))}
    group.out_of = {("g", "a%d" % slot): float(group_out[slot]) for slot in range(len(volumes))}
    return [merchants_shares.room_left(expected, "g", "a%d" % source, "a%d" % destination, own_share, merchants_shares.RouteShares(),
                                       group, float(held[destination]))
            for destination, source in zip(destinations, sources)]
