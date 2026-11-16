"""The goods market's kernels (goods_market_kernels.py, price_setting_kernel.py) against the numpy and Python rules they
replaced, kept here as the reference: the logit allocation of a market (`allocate`), a seller's price search
(`best_price`, `best_prices`) and the sold-out sellers' raise of asks (`demand_search.raise_asks`), on random books.

The kernels sum left to right where the old code used a pairwise sum, `fsum` or `numpy.sum`, so figures agree to rounding,
not bit for bit: the tolerance is a relative RELATIVE with a floor of ABSOLUTE for figures that are zero in one and a
float residue in the other."""
QUICK_TOPIC = True

import math
import random
import unittest
from itertools import groupby
from typing import List

import numpy

from sim.book import ROUNDING_SHARE
from sim.economy import demand_search, goods_market, price_setting
from sim.economy.goods_market_demand import DemandSchedule
from sim.economy.goods_market_logit import allocate
from sim.economy.price_setting import LOGIT_INTENSITY
from sim.economy.types import Bid, Offer

GOOD, AREA = "grain", "area"
RELATIVE = 1e-9
ABSOLUTE = 1e-9


# ---- the old numpy allocation, as it was in goods_market_logit.py -------------------------------------------------

def _old_weights(asks, stocked, ceilings):
    weights = numpy.zeros(len(asks))
    if stocked.any():
        cheapest = asks[numpy.argmax(stocked)]
        if cheapest > 0.0:
            weights[stocked] = numpy.exp(-LOGIT_INTENSITY * numpy.log(asks[stocked] / cheapest))
        else:
            weights[stocked] = (asks[stocked] <= cheapest).astype(float)
    running = numpy.concatenate(([0.0], numpy.cumsum(weights)))
    sums = running[numpy.searchsorted(asks, ceilings, side="right")]
    return weights, numpy.where(sums > 0.0, sums, 1.0)


def _old_serve(requests, left, tiers):
    totals = requests.sum(axis=1)
    over = numpy.nonzero(totals > left)[0]
    after = left - totals
    if not len(over):
        return requests, after, numpy.zeros_like(requests)
    served = requests.copy()
    wanted = requests[over]
    remaining = left[over]
    tier_totals = numpy.add.reduceat(wanted, [start for start, _end in tiers], axis=1)
    for tier, (start, end) in enumerate(tiers):
        total = tier_totals[:, tier]
        enough = remaining >= total
        share = numpy.where(total > 0.0, numpy.where(enough, 1.0, remaining / numpy.where(total > 0.0, total, 1.0)), 0.0)
        served[over, start:end] = wanted[:, start:end] * share[:, None]
        remaining = numpy.where(enough, remaining - total, 0.0)
    after[over] = 0.0
    short = numpy.zeros_like(requests)
    gap = requests[over] - served[over]
    short[over] = numpy.where(gap > ROUNDING_SHARE * requests[over], gap, 0.0)
    return served, after, short


def _old_affordable(prices, budgets_left):
    positive = prices > 0.0
    units = budgets_left[None, :] / numpy.where(positive, prices, 1.0)[:, None]
    return numpy.where(positive[:, None], units, numpy.inf)


def old_allocate(bids, offers, asks, schedule):
    """The numpy form of the rule: what a round could not serve is sent on as a share of the buyer's choice, and the quantity asked
    for is what was taken and what was still unmet at the end."""
    prices = numpy.array(asks, dtype=float)
    quantities = numpy.array([offer.quantity for offer in offers], dtype=float)
    ceilings = schedule.maximum_array()
    tiers, start = [], 0
    for _priority, group in groupby(bids, key=lambda bid: bid.priority):
        end = start + sum(1 for _ in group)
        tiers.append((start, end))
        start = end
    wants = schedule.matrix_at(prices)
    left = quantities.copy()
    stocked = left > ROUNDING_SHARE * quantities
    weights, sums = _old_weights(prices, stocked, ceilings)
    requests = wants * weights[:, None] / sums[None, :]
    served, left, short = _old_serve(requests, left, tiers)
    flow = served.copy()
    taken = served.sum(axis=0)
    cost = prices @ served
    unmet = short.sum(axis=0)
    budgets = numpy.array([bid.budget for bid in bids], dtype=float)
    for _round in range(len(offers)):
        stocked = left > ROUNDING_SHARE * quantities
        if not stocked.any() or not (unmet > 0.0).any():
            break
        weights, sums = _old_weights(prices, stocked, ceilings)
        unserved_share = numpy.where(wants > 0.0, short / numpy.where(wants > 0.0, wants, 1.0), 0.0).sum(axis=0)
        again = numpy.minimum(unserved_share[None, :] * wants * weights[:, None] / sums[None, :],
                              _old_affordable(prices, numpy.maximum(0.0, budgets - cost)))
        again[:, unserved_share <= 0.0] = 0.0
        served, left, short = _old_serve(again, left, tiers)
        flow += served
        taken = taken + served.sum(axis=0)
        cost = cost + prices @ served
        unmet = short.sum(axis=0)
    requested = float(taken.sum() + unmet.sum())
    return taken, cost, quantities - left, requested, flow


# ---- the old Python price search, as it was in price_setting.py -------------------------------------------------

def old_best_price(current, unit_value, market_size, rivals, stock, floor, ceiling, intensity=LOGIT_INTENSITY):
    best, best_earnings = current, price_setting.expected_earnings(
        current, unit_value, market_size * price_setting.logit_share(current, rivals, intensity), stock)
    for candidate in sorted({min(max(price, floor), ceiling) for price in price_setting.grid_prices(current)}):
        if candidate <= 0.0:
            continue
        earnings = price_setting.expected_earnings(
            candidate, unit_value, market_size * price_setting.logit_share(candidate, rivals, intensity), stock)
        if earnings > best_earnings + 1e-12 * max(abs(best_earnings), 1e-300):
            best, best_earnings = candidate, earnings
    return best


# ---- the old bisection of demand_search.raise_asks ------------------------------------------------------------

def old_first_round_requests(offers, asks, schedule):
    """What the buyers ask for at the asks before any seller runs out (the search for the level that sells the stock reads this)."""
    prices = numpy.array(asks, dtype=float)
    quantities = numpy.array([offer.quantity for offer in offers], dtype=float)
    weights, sums = _old_weights(prices, quantities > ROUNDING_SHARE * quantities, schedule.maximum_array())
    return float((schedule.matrix_at(prices) * weights[:, None] / sums[None, :]).sum())


def old_demand_covers(buyers, offers):
    supply = math.fsum(offer.quantity for offer in offers if offer.quantity > 0.0)
    ordered = goods_market.in_clearing_order(offers)
    asks = goods_market._asks(buyers, ordered)
    requested = 0.0
    if ordered and buyers.schedule.total_at(asks[0]) > 0.0 and supply > ROUNDING_SHARE * buyers.schedule.total_at(asks[0]):
        requested = old_first_round_requests(ordered, asks, buyers.schedule)
    return requested >= supply * (1.0 - ROUNDING_SHARE)


def old_raise_asks(buyers, offers, raisable, limits=None):
    offers = list(offers)
    if not raisable or not old_demand_covers(buyers, offers):
        return offers
    lowest = min(offers[index].reservation_price for index in raisable)
    supply = math.fsum(offer.quantity for offer in offers if offer.quantity > 0.0)
    ceiling = demand_search.price_ceiling(buyers, supply)
    if lowest <= 0.0 or not math.isfinite(ceiling) or ceiling <= lowest:
        return offers
    if limits:
        ceiling = min(ceiling, max(limits.get(index, math.inf) for index in raisable))
        if ceiling <= lowest:
            return offers
    low, high = lowest, ceiling
    if not old_demand_covers(buyers, demand_search._lifted(offers, raisable, lowest * (1.0 + demand_search.SEARCH_PRECISION), limits)):
        return offers
    while high / low - 1.0 > demand_search.SEARCH_PRECISION:
        middle = math.sqrt(low) * math.sqrt(high)
        if old_demand_covers(buyers, demand_search._lifted(offers, raisable, middle, limits)):
            low = middle
        else:
            high = middle
    return demand_search._lifted(offers, raisable, low, limits)


# ---- random books -------------------------------------------------------------------------------------------------

def random_bids(generator) -> List[Bid]:
    bids = [Bid("buyer%d" % index, GOOD, AREA, generator.choice(["tile", "other"]), generator.choice([0.0, 0.0, 2.0, 7.0]),
                generator.choice([0.0, generator.uniform(0.5, 30.0)]), generator.choice([1.0, generator.uniform(0.5, 3.0)]),
                generator.uniform(0.3, 2.0), generator.choice([0.0, generator.uniform(5.0, 400.0), 1e9]),
                generator.choice([0, 0, 1, 2]), generator.choice([1.5, 4.0, 1e9, math.inf]))
            for index in range(generator.randint(1, 9))]
    return sorted(bids, key=lambda bid: (bid.priority, bid.buyer, bid.tile))


def random_offers(generator) -> List[Offer]:
    return [Offer("seller%d" % index, GOOD, AREA, generator.choice(["tile", "tile", "other"]), generator.uniform(0.5, 40.0),
                  generator.choice([0.7, 1.0, 1.0, 1.6, 2.5, 4.0, 8.0]))
            for index in range(generator.randint(1, 7))]


def close(expected, actual) -> bool:
    return math.isclose(expected, actual, rel_tol=RELATIVE, abs_tol=ABSOLUTE)


class AllocationAgainstTheNumpyRuleTests(unittest.TestCase):
    def test_random_markets_allocate_alike(self):
        generator = random.Random(11)
        rounds_used = 0
        for _case in range(400):
            bids, offers = random_bids(generator), random_offers(generator)
            if generator.random() < 0.15:
                offers[0] = Offer("free", GOOD, AREA, "tile", 3.0, generator.choice([0.0, -1.0]))
            offers = sorted(offers, key=lambda offer: (offer.reservation_price, offer.seller))
            asks = [offer.reservation_price for offer in offers]
            schedule = DemandSchedule(bids)
            expected = old_allocate(bids, offers, asks, schedule)
            actual = allocate(bids, offers, asks, schedule)
            self.assertTrue(close(expected[3], actual.requested), (expected[3], actual.requested))
            for old, new in ((expected[0], actual.quantity), (expected[1], actual.cost), (expected[2], actual.sold)):
                self.assertEqual(len(old), len(new))
                for figure, other in zip(old.tolist(), new):
                    self.assertTrue(close(figure, other), (figure, other))
            self.assertTrue(numpy.allclose(expected[4], actual.flow, rtol=RELATIVE, atol=ABSOLUTE))
            rounds_used += expected[0].sum() > expected[4].sum(axis=0).sum() * 0.0
        self.assertGreater(rounds_used, 0)


class PriceSearchAgainstThePythonRuleTests(unittest.TestCase):
    def test_a_sellers_best_price_is_the_old_one(self):
        generator = random.Random(3)
        moved = 0
        for _case in range(600):
            rivals = [(generator.uniform(0.6, 2.0), generator.choice([1.0, 1.0, 3.0])) for _rival in range(generator.randint(0, 6))]
            current = generator.uniform(0.8, 1.8)
            value = generator.uniform(0.3, 1.2)
            kwargs = dict(unit_value=value, market_size=generator.uniform(10.0, 500.0), rivals=rivals,
                          stock=generator.choice([1.0, 20.0, 400.0]), floor=value, ceiling=max(value, generator.uniform(1.0, 3.0)))
            expected = old_best_price(current, **kwargs)
            actual = price_setting.best_price(current, **kwargs)
            moved += expected != current
            self.assertTrue(math.isclose(expected, actual, rel_tol=1e-12), (expected, actual))
        self.assertGreater(moved, 50)

    def test_a_markets_sellers_priced_together_are_priced_one_by_one(self):
        generator = random.Random(8)
        for _case in range(200):
            count = generator.randint(1, 6)
            asks = numpy.array([generator.uniform(0.6, 2.0) for _seller in range(count)])
            counts = numpy.array([generator.choice([0.0, 1.0, 3.0]) for _seller in range(count)])
            stock = numpy.array([generator.choice([1.0, 30.0, 400.0]) for _seller in range(count)])
            value = numpy.array([generator.uniform(0.3, 1.0) for _seller in range(count)])
            size = numpy.array([generator.uniform(10.0, 500.0) for _seller in range(count)])
            ceiling = value + generator.uniform(0.5, 2.0)
            together = price_setting.best_prices(asks, counts, numpy.arange(count), asks, value, size, stock, value, ceiling)
            for seller in range(count):
                rivals = [(asks[other], counts[other]) for other in range(count) if other != seller and counts[other] > 0.0]
                expected = old_best_price(asks[seller], value[seller], size[seller], rivals, stock[seller], value[seller],
                                          ceiling[seller])
                self.assertTrue(math.isclose(expected, together[seller], rel_tol=1e-12), (expected, together[seller]))


class RaiseAsksAgainstTheBisectionTests(unittest.TestCase):
    def test_random_sold_out_markets_are_raised_to_the_same_level(self):
        # a covered or uncovered verdict that differs in the last digit of the demand moves the bracket by one cell
        generator = random.Random(21)
        raised = 0
        for _case in range(250):
            bids = random_bids(generator)
            offers = [Offer(offer.seller, GOOD, AREA, offer.tile, offer.quantity * 0.2, offer.reservation_price)
                      for offer in random_offers(generator)]
            buyers = goods_market.Buyers(bids, generator.choice([None, 1.2]))
            raisable = [index for index in range(len(offers)) if generator.random() < 0.8]
            limits = {index: generator.uniform(1.0, 12.0) for index in raisable} if generator.random() < 0.5 else None
            expected = old_raise_asks(buyers, offers, raisable, limits)
            actual = demand_search.raise_asks(buyers, offers, raisable, limits)
            raised += expected != offers
            for old, new in zip(expected, actual):
                self.assertTrue(math.isclose(old.reservation_price, new.reservation_price,
                                             rel_tol=3 * demand_search.SEARCH_PRECISION), (old, new))
        self.assertGreater(raised, 20)


if __name__ == "__main__":
    unittest.main()
