"""The merchants' orders and credit request over the packed markets (`merchants_plan`) give what the per-route Python
path gave on random worlds: the same bids, offers and routes, the same shares committed, the same loan wanted.

The reference below is that path as it was (`merchants.candidate_routes` and `merchants.shared_room` per route). The
two agree to a relative 1e-9: the kernel adds held stock by slot, the reference by good, so the sums differ in the
last digits. A case where the reference itself jumps under a one-ulp nudge of its input (a rank tie or a room
sitting on zero decided by those digits) is not counted, and most cases must agree."""

QUICK_TOPIC = True

import math
import random
import unittest

from sim.economy import merchants, merchants_book, merchants_plan, merchants_transit
from sim.economy.merchants import Merchant
from sim.economy.order_rows import OrderRows
from sim.economy.protocols import AgentOrders
from sim.economy.types import Bid, GoodSpec, MarketArea
from sim.tests.economy_view_defaults import ViewDefaults

TILES = tuple("t%d" % number for number in range(8))
SPECS = {"g%d" % number: GoodSpec("g%d" % number, 500.0 + 300.0 * number, 0.1 * number, 0.0, "food") for number in range(3)}
PARTS = {"g0": 1, "g1": 2, "g2": 3}      # tiles to a market area: the goods sit on different partitions
TOLERANCE = 1e-9
SEEDS = 60


class LineCarriage:
    scale = 1.0

    def __init__(self, rate, days_per_step):
        self.rate, self.days_per_step = rate, days_per_step
        self.tables = {}

    def costs_from(self, source):
        if source not in self.tables:
            self.tables[source] = {tile: abs(TILES.index(tile) - TILES.index(source)) * self.rate for tile in TILES}
        return self.tables[source]

    def days_between(self, from_tile, to_tile):
        return abs(TILES.index(from_tile) - TILES.index(to_tile)) * self.days_per_step


class StubAreaMap:
    def __init__(self):
        self.by_good = {}
        for good, width in PARTS.items():
            groups = [TILES[start:start + width] for start in range(0, len(TILES), width)]
            self.by_good[good] = tuple(MarketArea("%s@%s" % (group[0], good), good, group, group[0]) for group in groups)

    def goods(self):
        return tuple(sorted(self.by_good))

    def areas(self, good):
        return self.by_good[good]

    def area_of(self, good, tile):
        for area in self.by_good[good]:
            if tile in area.tiles:
                return area.area_id
        raise KeyError(tile)


class View(ViewDefaults):
    year = 1

    def __init__(self, prices):
        self.prices = prices

    def price(self, good, area):
        return self.prices.get((good, area))


def random_world(seed):
    """(merchant, view, carriage, area map, held stock, group shares) from a seed."""
    rng = random.Random(seed)
    area_map = StubAreaMap()
    carriage = LineCarriage(rng.uniform(0.05, 1.0), rng.choice((60.0, 200.0, 400.0)))
    expected_prices, expected_volumes, view_prices = {}, {}, {}
    for good in PARTS:
        base = rng.uniform(1.0, 20.0)
        for area in area_map.areas(good):
            key = (good, area.area_id)
            if rng.random() < 0.7:
                expected_prices[key] = base * rng.uniform(0.5, 2.5)
            if rng.random() < 0.8:
                view_prices[key] = base * rng.uniform(0.5, 2.5)
            if rng.random() < 0.7:
                expected_volumes[key] = rng.uniform(1.0, 200.0)
    who = Merchant("m1", rng.choice(TILES), "owner", 1000.0, expected_prices, expected_volumes)
    for _shipment in range(rng.randrange(3)):
        who.add_shipment(merchants_transit.Shipment(rng.choice(sorted(PARTS)), rng.uniform(1.0, 30.0), rng.choice(TILES), 1))
    held = {(rng.choice(sorted(PARTS)), rng.choice(TILES)): rng.uniform(0.0, 50.0) for _stock in range(rng.randrange(6))}
    shares = merchants.RouteShares()
    for good in PARTS:
        for source in area_map.areas(good):
            for destination in area_map.areas(good):
                if rng.random() < 0.15:
                    shares.commit(good, source.area_id, destination.area_id, rng.uniform(0.0, 40.0))
    return who, View(view_prices), carriage, area_map, held, shares


def close(first, second):
    return math.isclose(first, second, rel_tol=TOLERANCE, abs_tol=1e-12)


def same_orders(left, right):
    if len(left.bids) != len(right.bids) or len(left.offers) != len(right.offers):
        return False
    for first, second in zip(left.bids, right.bids):
        if (first.buyer, first.good, first.area, first.tile) != (second.buyer, second.good, second.area, second.tile):
            return False
        if not all(close(a, b) for a, b in ((first.flexible_quantity, second.flexible_quantity),
                                            (first.reference_price, second.reference_price),
                                            (first.budget, second.budget), (first.maximum_price, second.maximum_price))):
            return False
    return all((a.seller, a.good, a.area, a.tile) == (b.seller, b.good, b.area, b.tile) and close(a.quantity, b.quantity)
               and close(a.reservation_price, b.reservation_price) for a, b in zip(left.offers, right.offers))


def same_routes(left, right):
    return left.keys() == right.keys() and all(
        len(left[key]) == len(right[key]) and all(a[:2] == b[:2] and close(a[2], b[2]) for a, b in zip(left[key], right[key]))
        for key in left)


class MerchantPlanTests(unittest.TestCase):
    def test_orders_agree_with_the_per_route_path(self):
        compared = with_bids = with_held_routes = 0
        for seed in range(SEEDS):
            who, view, carriage, area_map, held, shares = random_world(seed)
            cash = random.Random(seed).choice((0.0, 50.0, 3000.0, 1e6))
            reference_shares = merchants.RouteShares()
            reference_shares.into, reference_shares.out_of = dict(shares.into), dict(shares.out_of)
            expected = old_orders(who, view, carriage, area_map, cash, held, SPECS, 0.05, reference_shares)
            expected_routes = dict(who.routes)
            packed = merchants_plan.orders(who, view, carriage, area_map, cash, held, SPECS, 0.05, shares)
            if not same_orders(packed, expected) or not same_routes(who.routes, expected_routes):
                continue
            compared += 1
            with_bids += bool(packed.bids)
            with_held_routes += any(key in held for key in who.routes)
            for table, reference in ((shares.into, reference_shares.into), (shares.out_of, reference_shares.out_of)):
                self.assertEqual(table.keys(), reference.keys())
                for key in table:
                    self.assertTrue(close(table[key], reference[key]), (seed, key))
        self.assertGreaterEqual(compared, SEEDS - 5)
        self.assertGreaterEqual(with_bids, SEEDS // 3)      # the cases are not all empty
        self.assertGreaterEqual(with_held_routes, 5)

    def test_rows_written_equal_the_orders_made_as_objects(self):
        with_bids = with_offers = 0
        for seed in range(SEEDS):
            cash = random.Random(seed).choice((0.0, 50.0, 3000.0, 1e6))
            who, view, carriage, area_map, held, shares = random_world(seed)
            made = merchants_plan.orders(who, view, carriage, area_map, cash, held, SPECS, 0.05, shares)
            who_again, view, carriage, area_map, held, shares = random_world(seed)
            rows = OrderRows(None)
            nothing = merchants_plan.orders(who_again, view, carriage, area_map, cash, held, SPECS, 0.05, shares, rows_out=rows)
            self.assertEqual((nothing.bids, nothing.offers), ((), ()))
            self.assertEqual(rows.buyer, [bid.buyer for bid in made.bids])
            self.assertEqual(list(zip(rows.bid_good, rows.bid_area, rows.bid_tile, rows.priority)),
                             [(bid.good, bid.area, bid.tile, bid.priority) for bid in made.bids])
            self.assertEqual(rows.figures, [(bid.floor_quantity, bid.flexible_quantity, bid.reference_price, bid.elasticity, bid.budget,
                                             bid.maximum_price) for bid in made.bids])
            self.assertEqual(list(zip(rows.seller, rows.offer_good, rows.offer_area, rows.offer_tile, rows.quantity, rows.reservation)),
                             [(offer.seller, offer.good, offer.area, offer.tile, offer.quantity, offer.reservation_price) for offer in made.offers])
            self.assertEqual(who.routes.keys(), who_again.routes.keys())
            with_bids += bool(made.bids)
            with_offers += bool(made.offers)
        self.assertGreaterEqual(with_bids, SEEDS // 3)
        self.assertGreaterEqual(with_offers, SEEDS // 3)

    def test_dense_shares_gather_what_rivals_commit(self):
        who, view, carriage, area_map, held, _shares = random_world(3)
        route = merchants_book.route_pass(view, carriage, area_map, SPECS)
        dense = merchants_book.DenseShares(route.book)
        plain = merchants.RouteShares()
        orders = merchants_plan.orders(who, view, carriage, area_map, 3000.0, held, SPECS, 0.05, dense, route)
        again = merchants_plan.orders(who, view, carriage, area_map, 3000.0, held, SPECS, 0.05, plain)
        self.assertTrue(same_orders(orders, again))
        self.assertTrue(orders.bids)
        for bid in orders.bids:
            self.assertGreater(dense.out_of[route.book.slot_of[(bid.good, bid.area)]], 0.0)
        self.assertEqual(int((dense.into > 0.0).sum()), len(plain.into))

    def test_credit_agrees_with_the_per_route_path(self):
        compared = 0
        for seed in range(SEEDS):
            who, view, carriage, area_map, held, _shares = random_world(seed)
            cash = random.Random(seed).choice((0.0, 50.0, 3000.0))
            limit = random.Random(seed + 1).choice((5.0, 80.0, 5000.0))
            wanted, gain = merchants_plan.credit_wanted(who, view, carriage, area_map, cash, held, SPECS, 0.05, limit)
            expected_wanted, expected_gain = old_credit(who, view, carriage, area_map, cash, held, SPECS, 0.05, limit)
            if close(wanted, expected_wanted) and close(gain, expected_gain):
                compared += 1
        self.assertGreaterEqual(compared, SEEDS - 5)

    def test_no_goods_gives_no_orders_and_no_loan(self):
        who = Merchant("m1", "t0", "owner", 10.0)
        carriage, area_map = LineCarriage(0.1, 60.0), StubAreaMap()
        empty = merchants_plan.orders(who, View({}), carriage, area_map, 100.0, {}, {}, 0.05)
        self.assertEqual((empty.bids, empty.offers), ((), ()))
        self.assertEqual(merchants_plan.credit_wanted(who, View({}), carriage, area_map, 100.0, {}, {}, 0.05, 50.0), (0.0, 0.0))


def old_credit(merchant, view, carriage, area_map, cash, held_stock, specs, interest_rate, limit):
    """`merchants_credit.credit_request` before the packed search: (wanted, gain)."""
    candidates = merchants.candidate_routes(merchant, view, carriage, area_map, held_stock, specs, interest_rate)
    remaining = max(0.0, cash)
    wanted, gain = 0.0, 0.0
    own, group = merchants.RouteShares(), merchants.RouteShares()
    held_index = merchants.held_by_good(held_stock)
    for rank, good, source, destination, _price_here, outlay, _ceiling in candidates:
        room = merchants.shared_room(merchant, good, source, destination, held_stock, own, group, held_index)
        paid_by_cash = min(remaining / outlay, room) if outlay > 0.0 else room
        remaining -= paid_by_cash * outlay
        extra = (room - paid_by_cash) * outlay
        if extra <= 0.0 or math.isnan(extra):
            own.commit(good, source.area_id, destination.area_id, paid_by_cash)
            group.commit(good, source.area_id, destination.area_id, paid_by_cash)
            continue
        extra = min(extra, limit - wanted)
        planned = paid_by_cash + (extra / outlay if outlay > 0.0 else 0.0)
        own.commit(good, source.area_id, destination.area_id, planned)
        group.commit(good, source.area_id, destination.area_id, planned)
        wanted += extra
        gain += extra * -rank
        if wanted >= limit:
            break
    return wanted, gain


def old_orders(merchant, view, carriage, area_map, cash, held_stock, specs, interest_rate, shares):
    """`merchants.orders` before the packed search: the offers and bids for the year."""
    own = merchants.RouteShares()
    merchant.routes = {}
    held_index = merchants.held_by_good(held_stock)
    remaining = max(0.0, cash) * (1.0 - merchants.BUDGET_SAFETY_SHARE)
    candidates = merchants.candidate_routes(merchant, view, carriage, area_map, held_stock, specs, interest_rate,
                                            None if remaining > 0.0 else held_index)
    held_sorted = {}
    held_rooms = {}
    held_best = {}
    no_commitments = merchants.RouteShares()
    for _rank, good, source, destination, *_rest in candidates:
        held_tiles = held_sorted.get(good)
        if held_tiles is None:
            held_tiles = held_sorted[good] = sorted(held_index.get(good, ()))
        for tile, quantity in held_tiles:
            if quantity > 0.0 and tile in source.tiles and tile != destination.anchor_tile:
                leg = (destination.anchor_tile, destination.area_id)
                held_best.setdefault((good, tile), leg)
                held_rooms.setdefault((good, tile), {})[leg] = merchants.shared_room(
                    merchant, good, source, destination, held_stock, no_commitments, shares, held_index)
    for key, rooms in held_rooms.items():
        weights = merchants.merchants_legs.held_weights(rooms) or {held_best[key]: 1.0}
        merchant.routes[key] = merchants.merchants_legs.from_weights(weights)
    offers = [offer for offer in merchants._holding_offers(merchant, view, area_map, held_stock, specs, interest_rate)
              if (offer.good, offer.tile) not in merchant.routes]
    bids = []
    bought = {}
    for _rank, good, source, destination, price_here, outlay, ceiling in candidates:
        if remaining <= 0.0:
            break
        quantity = min(remaining / outlay, merchants.shared_room(merchant, good, source, destination, held_stock, own, shares, held_index))
        if quantity <= 0.0:
            continue
        own.commit(good, source.area_id, destination.area_id, quantity)
        shares.commit(good, source.area_id, destination.area_id, quantity)
        leg = (destination.anchor_tile, destination.area_id)
        by_leg = bought.setdefault((good, source.anchor_tile), {})
        by_leg[leg] = by_leg.get(leg, 0.0) + quantity
        bids.append(Bid(merchant.agent_id, good, source.area_id, source.anchor_tile, 0.0, quantity,
                        price_here, merchants.MERCHANT_BID_ELASTICITY, quantity * price_here, maximum_price=ceiling))
        remaining -= quantity * outlay
    for key, by_leg in bought.items():
        merchant.routes[key] = merchants.merchants_legs.from_weights(by_leg)
    return AgentOrders(bids=tuple(bids), offers=tuple(offers))


if __name__ == "__main__":
    unittest.main()
