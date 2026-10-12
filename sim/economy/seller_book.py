"""One seller's clears of a market against the same rivals: what `goods_market.price_and_sold` gives for each
reservation the seller tries, without redoing the rivals' side every time.

The rivals are sorted, grouped by the price they sell from, and summed once. A trial then adds the seller's
own offer to that book (into an existing group or a new one), solves the crossing, and reads off what the
seller sells. Every sum is the `math.fsum` of the same quantities `price_and_sold` sums (an exactly rounded
sum does not depend on order), so the results are the same bit for bit.
"""
import bisect
import math
from operator import attrgetter
from typing import List, Optional, Tuple

from .accounts import ROUNDING_SHARE
from .goods_market import CHEAP_PASSES_PER_BID, Buyers, at_a_ceiling
from .goods_market_solve import solve_price
from .types import Offer

_QUANTITY = attrgetter("quantity")


class SellerBook:
    """The rivals of `offer` on one market, ready for any number of trial reservations of `offer`."""

    def __init__(self, buyers: Buyers, rivals_in_clearing_order: List[Offer], offer: Offer):
        self.buyers = buyers
        self.seller = offer.seller
        self.own_quantity = offer.quantity
        minimum_price = buyers.minimum_price
        self.minimum_price = minimum_price
        self.quantities = list(map(_QUANTITY, rivals_in_clearing_order))
        self.reservations: List[float] = []      # one per group of rivals selling from the same price
        self.group_members: List[List[float]] = []
        self.group_own: List[List[float]] = []   # the quantities in each group that belong to the seller
        self.group_start: List[int] = []         # index in `quantities` of each group's first offer
        for index, rival in enumerate(rivals_in_clearing_order):
            reservation = max(rival.reservation_price, minimum_price)
            if not self.reservations or self.reservations[-1] != reservation:
                self.reservations.append(reservation)
                self.group_members.append([])
                self.group_own.append([])
                self.group_start.append(index)
            self.group_members[-1].append(rival.quantity)
            if rival.seller == self.seller:
                self.group_own[-1].append(rival.quantity)
        self.group_totals = [math.fsum(members) for members in self.group_members]
        self.group_start.append(len(self.quantities))

    def sold_and_price(self, reservation: Optional[float]) -> Tuple[float, float]:
        """(what the seller sells, clearing price) with its offer at `reservation`; None: no offer."""
        buyers = self.buyers
        last_price = buyers.last_price
        held_price = last_price if last_price is not None else 0.0
        quantity = self.own_quantity
        reservations, totals, own = self.reservations, self.group_totals, self.group_own
        offered_quantities = self.quantities
        has_own = reservation is not None and quantity > 0.0
        effective = math.inf
        if has_own:
            effective = max(reservation, self.minimum_price)
            group = bisect.bisect_left(reservations, effective)
            if group < len(reservations) and reservations[group] == effective:
                totals = totals[:group] + [math.fsum([*self.group_members[group], quantity])] + totals[group + 1:]
                own = own[:group] + [[*own[group], quantity]] + own[group + 1:]
            else:
                reservations = reservations[:group] + [effective] + reservations[group:]
                totals = totals[:group] + [quantity] + totals[group:]
                own = own[:group] + [[quantity]] + own[group:]
            offered_quantities = [*offered_quantities, quantity]
        if not reservations:
            return 0.0, held_price

        schedule = buyers.schedule
        lowest = reservations[0]
        demand_at_first = schedule.total_at(lowest)
        if math.fsum(offered_quantities) <= ROUNDING_SHARE * demand_at_first:
            return 0.0, held_price
        if demand_at_first <= 0.0:
            return 0.0, held_price if last_price is not None and lowest <= last_price else lowest

        levels, running = [], 0.0
        for level, total in zip(reservations, totals):
            running += total
            levels.append((level, running))
        price = solve_price(levels, schedule.total_at, demand_at_first,
                            schedule.uncapped_at if schedule.distinct_schedules() * CHEAP_PASSES_PER_BID
                            <= len(buyers.bids) else None, schedule.solutions)
        if schedule.price_capped:
            price = at_a_ceiling(price, schedule, levels, lowest)

        eligible_groups = bisect.bisect_right(reservations, price)
        eligible_rivals = self.group_start[bisect.bisect_right(self.reservations, price)]
        eligible_quantities = self.quantities[:eligible_rivals]
        if effective <= price:
            eligible_quantities.append(quantity)
        supply = math.fsum(eligible_quantities)
        remaining = buyers.traded_at(price, supply)
        sold: List[float] = []
        for total, quantities in zip(totals[:eligible_groups], own):
            if remaining >= total:
                sold.extend(quantities)
                remaining -= total
            else:
                share = remaining / total if total > 0.0 else 0.0
                sold.extend(each * share for each in quantities)
                break
        return math.fsum(each for each in sold if each > 0.0), price
