"""A good's cleared batch written into the order tables in one kernel call: the offers' final reservation, ask, units sold and left
and rank, the bids' units, cost and place in their market's clearing order, and the batch's rows appended to the bid order, offer
order, pairs and results tables (`goods_table_clear.write_offers`, `write_bids` and `record_batch` made about twenty numpy calls
per good). The caller reserves room in the four appended tables first."""
import numpy

from sim.jit import njit


@njit
def write_batch(bids, offers, bid_order, offer_order, pairs, results, market_ids, bid_rows, bid_ptr, offer_rows, offer_ptr, final,
                allocated_offers, allocated_bids, allocated_markets, pair_ptr, pair_bid, pair_offer, pair_quantity):
    """Write the allocation of the batch's markets. `allocated_offers` is (ask, sold, left, rank) per offer, `allocated_bids`
    (units, cost) per bid, `allocated_markets` (traded flag, requested, traded, mean ask, supply) per market, all in the order of
    `offer_rows`, `bid_rows` and `market_ids`; the pairs name bid and offer places within the batch, cut by market with `pair_ptr`."""
    ask, sold, left, rank = allocated_offers
    bid_quantity, bid_cost = allocated_bids
    traded_flag, requested, traded, mean, supply = allocated_markets
    markets = len(market_ids)
    for place in range(len(offer_rows)):
        row = offer_rows[place]
        offers.reservation_price[row] = final[place]
        offers.ask[row] = ask[place]
        offers.quantity_sold[row] = sold[place]
        offers.quantity_left[row] = left[place]
        offers.rank[row] = rank[place]
    first_bid, first_offer, first_pair, first_result = (bid_order.row_count[0], offer_order.row_count[0], pairs.row_count[0],
                                                       results.row_count[0])
    for market in range(markets):
        for place in range(bid_ptr[market], bid_ptr[market + 1]):
            row = bid_rows[place]
            bids.quantity_bought[row] = bid_quantity[place]
            bids.cost[row] = bid_cost[place]
            bids.position[row] = place - bid_ptr[market]
            bid_order.bid_row[first_bid + place] = row
        for place in range(offer_ptr[market], offer_ptr[market + 1]):
            offer_order.offer_row[first_offer + place] = offer_rows[place]
        for pair in range(pair_ptr[market], pair_ptr[market + 1]):
            pairs.bid_row[first_pair + pair] = bid_rows[pair_bid[pair]]
            pairs.offer_row[first_pair + pair] = offer_rows[pair_offer[pair]]
            pairs.quantity[first_pair + pair] = pair_quantity[pair]
        slot = first_result + market
        results.market[slot] = market_ids[market]
        results.traded[slot] = traded_flag[market]
        results.quantity[slot] = traded[market]
        results.price[slot] = mean[market]
        results.demand_at_price[slot] = requested[market]
        results.offered_at_price[slot] = supply[market]
        results.first_bid_slot[slot] = first_bid + bid_ptr[market]
        results.bid_count[slot] = bid_ptr[market + 1] - bid_ptr[market]
        results.first_offer_slot[slot] = first_offer + offer_ptr[market]
        results.offer_count[slot] = offer_ptr[market + 1] - offer_ptr[market]
        results.first_pair[slot] = first_pair + pair_ptr[market]
        results.pair_count[slot] = pair_ptr[market + 1] - pair_ptr[market]
    bid_order.row_count[0] = first_bid + len(bid_rows)
    offer_order.row_count[0] = first_offer + len(offer_rows)
    pairs.row_count[0] = first_pair + len(pair_quantity)
    results.row_count[0] = first_result + markets
