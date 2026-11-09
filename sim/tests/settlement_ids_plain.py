"""The plain numpy rules `settlement_number_kernel` and `settlement_note_kernel` replaced (`settlement_ids` and `goods_settle` ran
them with a numpy call per step), kept so the kernels are tested against them."""
import numpy

from sim.economy.settlement_numbering import local_numbering


def pair_positions(pair_ptr, slots):
    starts, ends = pair_ptr[slots], pair_ptr[slots + 1]
    sizes = ends - starts
    total = int(sizes.sum())
    before = numpy.cumsum(sizes) - sizes
    return sizes, numpy.repeat(starts - before, sizes) + numpy.arange(total, dtype=numpy.int64)


def first_use_numbers(values):
    distinct, first, inverse = numpy.unique(values, return_index=True, return_inverse=True)
    order = numpy.argsort(first, kind="stable")
    rank = numpy.empty(len(distinct), dtype=numpy.int64)
    rank[order] = numpy.arange(len(distinct), dtype=numpy.int64)
    return rank[inverse.reshape(-1)], distinct[order]


def numbered_keys(pair_bid, pair_offer, bid_rows, offer_rows, positions, tile_stride, empty_tile, bids, offers):
    bid_at, offer_at = pair_bid[positions], pair_offer[positions]
    bid_row, offer_row = bid_rows[bid_at], offer_rows[offer_at]
    buyer, buyer_tile = bids.buyer[bid_row], bids.tile[bid_row]
    seller, seller_tile = offers.seller[offer_row], offers.tile[offer_row]
    used_bids, used_offers = bid_rows[numpy.unique(bid_at)], offer_rows[numpy.unique(offer_at)]
    tileless = buyer_tile == empty_tile
    receipt_tile = numpy.where(tileless, seller_tile, buyer_tile)
    key_value = lambda holder, tile: holder * tile_stride + tile        # noqa: E731
    candidates = numpy.concatenate((key_value(bids.buyer[used_bids], bids.tile[used_bids]),
                                    key_value(offers.seller[used_offers], offers.tile[used_offers]),
                                    key_value(buyer[tileless], seller_tile[tileless])))
    _numbers, keys = first_use_numbers(candidates)
    sorted_order = numpy.argsort(keys, kind="stable")
    place_in = lambda values: sorted_order[numpy.searchsorted(keys[sorted_order], values)]      # noqa: E731
    receipt, sold_from = place_in(key_value(buyer, receipt_tile)), place_in(key_value(seller, seller_tile))
    holder, tile = keys // tile_stride, keys % tile_stride
    key_agent, agents = first_use_numbers(holder)
    return receipt, sold_from, holder, tile, key_agent, agents


def number_good(pair_ptr, slots, pair_bid, pair_offer, bid_rows, offer_rows, bids, offers, tile_stride, empty_tile):
    sizes, positions = pair_positions(pair_ptr, slots)
    receipt, sold_from, holder, tile, key_agent, agents = numbered_keys(
        pair_bid, pair_offer, bid_rows, offer_rows, positions, tile_stride, empty_tile, bids, offers)
    local = local_numbering(sizes, receipt, sold_from, key_agent, len(agents))
    return (positions, *local, holder, tile, agents, sold_from)


def note_columns(agent_offset, slots, agent, paid, got_goods, paid_as_buyer, buyer_net, goods_in, imports, exports, makers, sales_purpose,
                 good_number, code=(7, 9)):
    """The columns `goods_settle._noted_by_ids` built with numpy; `code` is the foreign purpose slot that `purpose_code` gave."""
    counts = numpy.diff(agent_offset)
    rows = int(agent_offset[-1])
    market_of_row = numpy.repeat(numpy.arange(len(counts), dtype=numpy.int64), counts)
    template, reference = numpy.zeros(rows, dtype=numpy.int64), numpy.zeros(rows, dtype=numpy.int64)
    foreign = (imports != 0.0) | (exports != 0.0)
    if foreign.any():
        for market in numpy.unique(market_of_row[foreign]).tolist():
            here = market_of_row == market
            template[here], reference[here] = code
    plant_bought = (paid > 0.0) & got_goods & numpy.isin(agent, makers)
    found = got_goods | paid_as_buyer
    bought = (numpy.repeat(numpy.array(slots, dtype=numpy.int64), counts)[found], agent[found], goods_in[found],
              numpy.where(paid_as_buyer[found], buyer_net[found], 0.0))
    return (numpy.full(rows, sales_purpose, dtype=numpy.int64), numpy.full(rows, good_number, dtype=numpy.int64), template, reference,
            plant_bought, bool(foreign.any()), *bought)
