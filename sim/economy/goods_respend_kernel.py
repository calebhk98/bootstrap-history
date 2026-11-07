"""The year's respend rounds as one numba kernel over every rationed household and every market (goods_respend_year.py is the
caller, goods_respend_pack.py packs the records and unpacks the answer).

A round: each buyer rationed of money places bids for the goods still offered (goods_respend_basket_kernel.buyer_bids), the
markets those bids go to clear in order against the stock left (the logit allocation of goods_market_kernels, the
rule of goods_market.clear) and settle at their sellers' asks against the purses and stocks as they stand (the rule of
settlement_kernel.settle_pairs), and what each buyer was rationed of there becomes the next round's money. The rounds
stop under `goods_respend.last_round_negligible`. Everything a market, a buyer or the ledger reads afterwards is returned as
arrays: a log of the bids and of the clearings by round and market, and of the pairs settled.
"""
import numpy

from sim.jit import njit

from .goods_market_kernels import KERNEL, allocate_arrays, total_wanted
from .goods_respend_basket_kernel import buyer_bids
from .goods_respend_market_kernel import lowest_ask, quantity_of, wanted_adding


@njit(**KERNEL)
def respend_rounds(buyer_agent, buyer_basket, buyer_area_row, buyer_key, has_bid, area_market, need_ptr, need_weight,
                   need_slot, need_has_limits, need_good_ptr, goods, effects, limits, limited, basket_exponent,
                   basket_substitution, basket_need_of_good, need_count, max_goods, market_good, offer_ptr,
                   offer_reservation, offer_quantity, offer_key, offer_agent, offer_order, market_last_price, market_has_last,
                   market_fallback, market_fallback_ok, key_stock, key_agent, agent_cash, agent_edge, agent_external,
                   agent_import, agent_export, first_market, first_buyer, first_floor, first_flexible,
                   first_reference, first_exponent, first_budget, first_maximum, first_units, first_money,
                   wanted_share, negligible_share, minimum_share, rounding_share, capacity):
    """Run the rounds. Mutates `has_bid`, `offer_quantity`, `key_stock` and `agent_cash` (their final state is the answer).

    Returns `overflow` (a log filled to `capacity`: run again with more), the counts of rows logged, then the logs: bids (round,
    market, buyer, flexible, reference, budget, ceiling, whether it adds demand), clearings (market, round, quantity traded,
    price, whether it has one, demand at price, offered, goods delivered), pairs (market, buyer, offer, goods, money, the
    agent whose foreign-money figure it is in as import and as export, -1 for none), and per market the wanted quantity
    added, goods delivered, offered and delivered in its last clearing, and whether it cleared."""
    buyers = len(buyer_agent)
    markets = len(market_good)
    good_count = area_market.shape[1]
    rationed = numpy.zeros((buyers, need_count))
    # the money each household was rationed of in the first round's clearings
    row = 0
    rows = len(first_market)
    while row < rows:
        market, buyer = first_market[row], first_buyer[row]
        last = row
        budget = 0.0
        while last < rows and first_market[last] == market and first_buyer[last] == buyer:
            budget += first_budget[last]
            last += 1
        need = basket_need_of_good[buyer_basket[buyer], market_good[market]]
        if need >= 0:
            units, money = first_units[row], first_money[row]
            ok = True
            if units > 0.0:
                price = money / units
            else:
                price = market_fallback[market]
                ok = market_fallback_ok[market]
            if ok and price > 0.0:
                wanted = 0.0
                for each in range(row, last):
                    wanted += quantity_of(price, first_floor[each], first_flexible[each], first_budget[each],
                                          first_reference[each], first_exponent[each], first_maximum[each])
                amount = min(budget - money, (wanted - units) * price)
                if amount > 0.0:
                    rationed[buyer, need] += amount
        row = last
    low_ask = numpy.zeros(markets)
    for market in range(markets):
        low_ask[market] = lowest_ask(offer_ptr[market], offer_ptr[market + 1], offer_reservation, offer_quantity)
    market_wanted = numpy.zeros(markets)
    market_delivered = numpy.zeros(markets)
    market_offered = numpy.zeros(markets)
    market_last_delivered = numpy.zeros(markets)
    market_cleared = numpy.zeros(markets, dtype=numpy.bool_)
    log_bid_round = numpy.zeros(capacity, dtype=numpy.int64)
    log_bid_market = numpy.zeros(capacity, dtype=numpy.int64)
    log_bid_buyer = numpy.zeros(capacity, dtype=numpy.int64)
    log_bid_flexible = numpy.zeros(capacity)
    log_bid_reference = numpy.zeros(capacity)
    log_bid_budget = numpy.zeros(capacity)
    log_bid_maximum = numpy.zeros(capacity)
    log_bid_adding = numpy.zeros(capacity, dtype=numpy.bool_)
    log_clear_market = numpy.zeros(capacity, dtype=numpy.int64)
    log_clear_round = numpy.zeros(capacity, dtype=numpy.int64)
    log_clear_quantity = numpy.zeros(capacity)
    log_clear_price = numpy.zeros(capacity)
    log_clear_has_price = numpy.zeros(capacity, dtype=numpy.bool_)
    log_clear_demand = numpy.zeros(capacity)
    log_clear_offered = numpy.zeros(capacity)
    log_clear_delivered = numpy.zeros(capacity)
    log_pair_market = numpy.zeros(capacity, dtype=numpy.int64)
    log_pair_buyer = numpy.zeros(capacity, dtype=numpy.int64)
    log_pair_offer = numpy.zeros(capacity, dtype=numpy.int64)
    log_pair_goods = numpy.zeros(capacity)
    log_pair_money = numpy.zeros(capacity)
    log_pair_import = numpy.zeros(capacity, dtype=numpy.int64)
    log_pair_export = numpy.zeros(capacity, dtype=numpy.int64)
    bids_logged = 0
    clears_logged = 0
    pairs_logged = 0

    shares = numpy.zeros(len(goods))
    ceilings = numpy.zeros(len(goods))
    priced = numpy.zeros(len(goods), dtype=numpy.bool_)
    units_scratch = numpy.zeros(len(goods))
    fixed_value = numpy.zeros(len(goods))
    fixed_flag = numpy.zeros(len(goods), dtype=numpy.bool_)
    spend = numpy.zeros(good_count)
    ceiling = numpy.zeros(good_count)
    touched = numpy.zeros(good_count, dtype=numpy.bool_)
    ask_of_good = numpy.zeros(good_count)
    out_good = numpy.zeros(good_count, dtype=numpy.int64)
    out_spend = numpy.zeros(good_count)
    out_ceiling = numpy.zeros(good_count)
    money_local = numpy.zeros(need_count)
    per_round = max(1, buyers * max_goods)
    gen_market = numpy.zeros(per_round, dtype=numpy.int64)
    gen_buyer = numpy.zeros(per_round, dtype=numpy.int64)
    gen_amount = numpy.zeros(per_round)
    gen_ask = numpy.zeros(per_round)
    gen_ceiling = numpy.zeros(per_round)
    placed = numpy.zeros(per_round, dtype=numpy.int64)
    starts = numpy.zeros(markets + 1, dtype=numpy.int64)
    asked = numpy.zeros(len(key_stock))
    key_sold = numpy.zeros(len(key_stock))
    stock_walk = numpy.zeros(len(key_stock))
    given_sum = numpy.zeros(len(key_stock))
    taken_sum = numpy.zeros(len(key_stock))
    cash_walk = numpy.zeros(len(agent_cash))
    paid_sum = numpy.zeros(len(agent_cash))
    received_sum = numpy.zeros(len(agent_cash))
    owed = numpy.zeros(len(agent_cash))
    paid_so_far = 0.0
    overflow = False

    for round_number in range(markets + 1):
        count = 0
        for buyer in range(buyers):
            total = 0.0
            for need in range(need_count):
                if rationed[buyer, need] > 0.0:
                    total += rationed[buyer, need]
            if total <= 0.0:
                continue
            cash = agent_cash[buyer_agent[buyer]]
            if cash <= 0.0:
                continue
            basket = buyer_basket[buyer]
            first_need = need_ptr[basket]
            for slot in range(need_ptr[basket + 1] - first_need):
                amount = rationed[buyer, need_slot[first_need + slot]]
                if total > cash:
                    amount = amount * cash / total
                money_local[slot] = amount
            for good in range(good_count):
                market = area_market[buyer_area_row[buyer], good]
                ask_of_good[good] = low_ask[market] if market >= 0 else numpy.nan
            spent = buyer_bids(basket, money_local, need_ptr, need_weight, need_has_limits, need_good_ptr, goods, effects,
                               limits, limited, basket_exponent[basket], ask_of_good, shares, ceilings, priced,
                               units_scratch, fixed_value, fixed_flag, spend, ceiling, touched, out_good, out_spend,
                               out_ceiling)
            for index in range(spent):
                good = out_good[index]
                gen_market[count] = area_market[buyer_area_row[buyer], good]
                gen_buyer[count] = buyer
                gen_amount[count] = out_spend[index]
                gen_ask[count] = ask_of_good[good]
                gen_ceiling[count] = out_ceiling[index]
                count += 1
        for slot in range(markets + 1):
            starts[slot] = 0
        for bid in range(count):
            starts[gen_market[bid] + 1] += 1
        for slot in range(markets):
            starts[slot + 1] += starts[slot]
        filled = starts[:markets].copy()
        for bid in range(count):
            placed[filled[gen_market[bid]]] = bid
            filled[gen_market[bid]] += 1
        rationed[:, :] = 0.0
        any_rationed = False
        paid_this_round = 0.0
        for market in range(markets):
            first, last = starts[market], starts[market + 1]
            bids = last - first
            if bids == 0:
                continue
            if bids_logged + bids > capacity or clears_logged + 1 > capacity:
                overflow = True
                break
            floors = numpy.zeros(bids)
            flexibles = numpy.zeros(bids)
            budgets = numpy.zeros(bids)
            references = numpy.zeros(bids)
            exponents = numpy.zeros(bids)
            maximums = numpy.zeros(bids)
            adding = numpy.zeros(bids, dtype=numpy.bool_)
            scale = 0.0
            for position in range(bids):
                bid = placed[first + position]
                buyer = gen_buyer[bid]
                budgets[position] = gen_amount[bid]
                references[position] = gen_ask[bid]
                flexibles[position] = gen_amount[bid] / gen_ask[bid]
                exponents[position] = -basket_substitution[buyer_basket[buyer]]
                maximums[position] = gen_ceiling[bid]
                adding[position] = not has_bid[market, buyer]
                scale += gen_ask[bid]
            minimum = minimum_share * scale / bids
            capped = False
            for position in range(bids):
                if maximums[position] < numpy.inf:
                    capped = True
            before = low_ask[market]
            # the market's offers with stock, in clearing order (cheapest reservation first)
            active = 0
            supply = 0.0
            for offer in range(offer_ptr[market], offer_ptr[market + 1]):
                if offer_quantity[offer] > 0.0:
                    active += 1
                    supply += offer_quantity[offer]
            offers = numpy.zeros(active, dtype=numpy.int64)
            asks = numpy.zeros(active)
            quantities = numpy.zeros(active)
            slot = 0
            for offer in range(offer_ptr[market], offer_ptr[market + 1]):
                if offer_quantity[offer] > 0.0:
                    offers[slot] = offer
                    asks[slot] = max(offer_reservation[offer], minimum)
                    quantities[slot] = offer_quantity[offer]
                    slot += 1
            trades = False
            if active > 0:
                wanted_first = total_wanted(asks[0], floors, flexibles, budgets, references, exponents, maximums, capped)
                trades = wanted_first > 0.0 and supply > rounding_share * wanted_first
            traded = 0.0
            requested = 0.0
            mean = 0.0
            sold = numpy.zeros(active)
            flow = numpy.zeros((active, bids))
            if trades:
                bounds = numpy.zeros(2, dtype=numpy.int64)
                bounds[1] = bids
                taken, cost, sold, requested, flow = allocate_arrays(asks, quantities, floors, flexibles, budgets,
                                                                     references, exponents, maximums, capped, bounds)
                weighted = 0.0
                for slot in range(active):
                    if sold[slot] > 0.0:
                        traded += sold[slot]
                        weighted += sold[slot] * asks[slot]
                if traded > 0.0:
                    mean = weighted / traded
            for position in range(bids):
                bid = placed[first + position]
                log_bid_round[bids_logged] = round_number
                log_bid_market[bids_logged] = market
                log_bid_buyer[bids_logged] = gen_buyer[bid]
                log_bid_flexible[bids_logged] = flexibles[position]
                log_bid_reference[bids_logged] = references[position]
                log_bid_budget[bids_logged] = budgets[position]
                log_bid_maximum[bids_logged] = maximums[position]
                log_bid_adding[bids_logged] = adding[position]
                bids_logged += 1
            log_clear_market[clears_logged] = market
            log_clear_round[clears_logged] = round_number
            log_clear_offered[clears_logged] = supply
            if traded > 0.0:
                log_clear_quantity[clears_logged] = traded
                log_clear_price[clears_logged] = mean
                log_clear_has_price[clears_logged] = True
                log_clear_demand[clears_logged] = requested
            else:
                if active == 0 or (market_has_last[market] and asks[0] <= market_last_price[market]):
                    log_clear_price[clears_logged] = market_last_price[market]
                    log_clear_has_price[clears_logged] = market_has_last[market]
                else:
                    log_clear_price[clears_logged] = asks[0]
                    log_clear_has_price[clears_logged] = True
            market_wanted[market] += wanted_adding(before, adding, wanted_share, requested, traded > 0.0, floors,
                                                   flexibles, budgets, references, exponents, maximums)
            for position in range(bids):
                has_bid[market, gen_buyer[placed[first + position]]] = True
            # settlement: pairs in offer-major order, scaled to the stock and purses, then walked
            units_got = numpy.zeros(bids)
            money_paid = numpy.zeros(bids)
            delivered = 0.0
            if traded > 0.0:
                pair_count = 0
                for slot in range(active):
                    for position in range(bids):
                        if flow[slot, position] > 0.0:
                            pair_count += 1
                if pairs_logged + pair_count > capacity:
                    overflow = True
                    break
                pair_slot = numpy.zeros(pair_count, dtype=numpy.int64)
                pair_bid = numpy.zeros(pair_count, dtype=numpy.int64)
                pair_amount = numpy.zeros(pair_count)
                pair = 0
                for slot in range(active):
                    for position in range(bids):
                        if flow[slot, position] > 0.0:
                            pair_slot[pair] = slot
                            pair_bid[pair] = position
                            pair_amount[pair] = flow[slot, position]
                            pair += 1
                for pair in range(pair_count):
                    asked[offer_key[offers[pair_slot[pair]]]] += pair_amount[pair]
                for pair in range(pair_count):
                    key = offer_key[offers[pair_slot[pair]]]
                    if asked[key] > key_stock[key] and not agent_edge[key_agent[key]]:
                        pair_amount[pair] *= max(key_stock[key], 0.0) / asked[key]
                for pair in range(pair_count):
                    asked[offer_key[offers[pair_slot[pair]]]] = 0.0
                for pair in range(pair_count):
                    payer = buyer_agent[gen_buyer[placed[first + pair_bid[pair]]]]
                    owed[payer] += pair_amount[pair] * asks[pair_slot[pair]]
                for pair in range(pair_count):
                    payer = buyer_agent[gen_buyer[placed[first + pair_bid[pair]]]]
                    if owed[payer] > agent_cash[payer] and not agent_edge[payer]:
                        pair_amount[pair] *= max(agent_cash[payer], 0.0) / owed[payer]
                for pair in range(pair_count):
                    owed[buyer_agent[gen_buyer[placed[first + pair_bid[pair]]]]] = 0.0
                for pair in range(pair_count):
                    stock_walk[offer_key[offers[pair_slot[pair]]]] = key_stock[offer_key[offers[pair_slot[pair]]]]
                    cash_walk[buyer_agent[gen_buyer[placed[first + pair_bid[pair]]]]] = \
                        agent_cash[buyer_agent[gen_buyer[placed[first + pair_bid[pair]]]]]
                for pair in range(pair_count):
                    amount = pair_amount[pair]
                    if amount <= 0.0:
                        continue
                    offer = offers[pair_slot[pair]]
                    buyer = gen_buyer[placed[first + pair_bid[pair]]]
                    payer = buyer_agent[buyer]
                    seller = offer_agent[offer]
                    key = offer_key[offer]
                    if not agent_edge[seller]:
                        if stock_walk[key] < amount:
                            amount = stock_walk[key]
                        stock_walk[key] -= amount
                    pay = amount * asks[pair_slot[pair]]
                    if not agent_edge[payer]:
                        if cash_walk[payer] < pay:
                            pay = cash_walk[payer]
                        cash_walk[payer] -= pay
                    given_sum[key] += amount
                    held = buyer_key[buyer, market_good[market]]
                    if held >= 0:
                        taken_sum[held] += amount
                    paid_sum[payer] += pay
                    received_sum[seller] += pay
                    delivered += amount
                    units_got[pair_bid[pair]] += amount
                    money_paid[pair_bid[pair]] += pay
                    importer, exporter = -1, -1
                    if pay > 0.0:
                        if agent_external[seller] and not agent_external[payer]:
                            importer = payer
                        elif agent_external[payer] and not agent_external[seller]:
                            exporter = seller
                        elif agent_import[seller]:
                            importer = seller
                        elif agent_export[payer]:
                            exporter = payer
                    log_pair_market[pairs_logged] = market
                    log_pair_buyer[pairs_logged] = buyer
                    log_pair_offer[pairs_logged] = offer
                    log_pair_goods[pairs_logged] = amount
                    log_pair_money[pairs_logged] = pay
                    log_pair_import[pairs_logged] = importer
                    log_pair_export[pairs_logged] = exporter
                    pairs_logged += 1
                # the purses and stocks become what the book makes of the summed settlement: start less out, plus in
                for pair in range(pair_count):
                    key = offer_key[offers[pair_slot[pair]]]
                    held = buyer_key[gen_buyer[placed[first + pair_bid[pair]]], market_good[market]]
                    for each in (key, held):
                        if each >= 0:
                            key_stock[each] = key_stock[each] - given_sum[each] + taken_sum[each]
                            given_sum[each] = 0.0
                            taken_sum[each] = 0.0
                    for each in (buyer_agent[gen_buyer[placed[first + pair_bid[pair]]]], offer_agent[offers[pair_slot[pair]]]):
                        agent_cash[each] = agent_cash[each] - paid_sum[each] + received_sum[each]
                        paid_sum[each] = 0.0
                        received_sum[each] = 0.0
                # what sold comes off the market's offers in their original order, a seller's sales by (seller, tile) first
                # to its first offers (goods_respend.offers_left)
                for slot in range(active):
                    key_sold[offer_key[offers[slot]]] += sold[slot]
                for index in range(offer_ptr[market], offer_ptr[market + 1]):
                    offer = offer_order[index]
                    if offer_quantity[offer] > 0.0:
                        key = offer_key[offer]
                        taken_now = min(offer_quantity[offer], key_sold[key])
                        key_sold[key] -= taken_now
                        left = offer_quantity[offer] - taken_now
                        offer_quantity[offer] = left if left > 0.0 else 0.0
                for slot in range(active):
                    key_sold[offer_key[offers[slot]]] = 0.0
            log_clear_delivered[clears_logged] = delivered
            clears_logged += 1
            for position in range(bids):
                paid_this_round += money_paid[position]
            market_delivered[market] += delivered
            market_offered[market] = supply
            market_last_delivered[market] = delivered
            market_cleared[market] = True
            low_ask[market] = lowest_ask(offer_ptr[market], offer_ptr[market + 1], offer_reservation, offer_quantity)
            # what each buyer was rationed of here, to spend next round
            for position in range(bids):
                bid = placed[first + position]
                buyer = gen_buyer[bid]
                need = basket_need_of_good[buyer_basket[buyer], market_good[market]]
                if need < 0:
                    continue
                units, money = units_got[position], money_paid[position]
                ok = True
                if units > 0.0:
                    price = money / units
                else:
                    price = low_ask[market]
                    ok = price == price
                if ok and price > 0.0:
                    wanted = quantity_of(price, floors[position], flexibles[position], budgets[position],
                                         references[position], exponents[position], maximums[position])
                    amount = min(budgets[position] - money, (wanted - units) * price)
                    if amount > 0.0:
                        rationed[buyer, need] += amount
                        any_rationed = True
        if overflow:
            break
        paid_so_far += paid_this_round
        if paid_this_round <= 0.0 or paid_this_round < negligible_share * paid_so_far or not any_rationed:
            break
    return (overflow, bids_logged, clears_logged, pairs_logged, log_bid_round, log_bid_market, log_bid_buyer,
            log_bid_flexible, log_bid_reference, log_bid_budget, log_bid_maximum, log_bid_adding, log_clear_market,
            log_clear_round, log_clear_quantity, log_clear_price, log_clear_has_price, log_clear_demand,
            log_clear_offered, log_clear_delivered, log_pair_market, log_pair_buyer, log_pair_offer, log_pair_goods,
            log_pair_money, log_pair_import, log_pair_export, market_wanted, market_delivered, market_offered,
            market_last_delivered, market_cleared)
