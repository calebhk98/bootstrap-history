"""`goods_settle.note_clearings`' choice of the markets whose fills the ledger keeps, as numpy chains over the good's clearing columns (what
`goods_round_notes_kernel.markets_with_fills` replaced)."""
import numpy

from sim.economy.goods_good_clear import ON_OBJECTS, TABLE_TRADED


def plain_places_with_fills(way, slots, bid_ptr, watched, watchers_set) -> list:
    """The markets (in clearing order) whose fills the ledger may keep: those on objects, and those traded in the batch where a watcher's bid
    took units (`watched` per bid, None: the watchers bought nothing); with no watchers set every market that traded."""
    objects = way == ON_OBJECTS
    traded = numpy.flatnonzero(way == TABLE_TRADED)
    if watchers_set and len(traded):
        if watched is None:
            traded = traded[:0]
        else:
            counted = numpy.concatenate(([0], numpy.cumsum(watched)))
            chosen = slots[traded]
            traded = traded[counted[bid_ptr[chosen + 1]] > counted[bid_ptr[chosen]]]
    objects[traded] = True
    return numpy.flatnonzero(objects).tolist()
