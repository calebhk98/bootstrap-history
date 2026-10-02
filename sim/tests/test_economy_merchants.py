"""Merchants carry goods between market areas when the price gap beats carriage, interest, spoilage and a
margin; capital and market share limit them; several chasing one gap overshoot it."""
import unittest

from sim.economy import goods_market, merchants, settlement
from sim.economy.accounts import Book
from sim.economy.market_areas import AreaMap
from sim.economy.merchants import Merchant
from sim.economy.tile_costs import CarriageTable, Edge
from sim.economy.types import EDGE_MINT, EDGE_PRODUCTION, Bid, Fill, GoodsMove, GoodSpec, Offer, Transfer

TILES = ("a", "b")
CARRIAGE_PER_UNIT = 1.0         # one-tonne units, 100 km at 0.01 a tonne-km
INTEREST_RATE = 0.05
SPECS = {
    "salt": GoodSpec("salt", 1000.0, 0.0, 0.0, "food"),
    "fish": GoodSpec("fish", 1000.0, 0.5, 0.0, "food"),
}


class View:
    year = 1

    def __init__(self, prices):
        self.prices = prices

    def price(self, good, area):
        return self.prices.get((good, area))


def world(spec_goods=("salt",)):
    carriage = CarriageTable(TILES, [Edge("a", "b", ("land",), 100.0)], {"land": 0.01})
    goods = [(SPECS[good], 2.0) for good in spec_goods]
    area_map = AreaMap(TILES, carriage, goods, {"a": 10.0, "b": 5.0}, threshold_share=0.01)
    return carriage, area_map, {good: area_map.area_of(good, "a") for good in spec_goods}, \
        {good: area_map.area_of(good, "b") for good in spec_goods}


def merchant(name="m1", prices=None, volumes=None):
    return Merchant(name, "a", "owner", 100.0, dict(prices or {}), dict(volumes or {}))


def plan(who, price_a, price_b, cash=1000.0, good="salt", held=None, rate=0.0, volumes=True):
    carriage, area_map, area_a, area_b = world((good,))
    who.expected_prices = {(good, area_a[good]): price_a, (good, area_b[good]): price_b}
    if volumes:
        who.expected_volumes = {(good, area_b[good]): 100.0}
    return merchants.orders(who, View({}), carriage, area_map, cash, held or {}, SPECS, rate)


class GapTests(unittest.TestCase):
    def test_no_trade_when_the_gap_is_below_carriage(self):
        self.assertEqual(plan(merchant(), 2.0, 2.9).bids, ())

    def test_no_trade_when_the_gap_equals_carriage_plus_margin(self):
        self.assertEqual(plan(merchant(), 2.0, 2.0 + CARRIAGE_PER_UNIT + merchants.MERCHANT_MARGIN_SHARE * 2.0).bids, ())

    def test_trade_when_the_gap_is_above_carriage(self):
        orders = plan(merchant(), 2.0, 4.0)
        self.assertEqual(len(orders.bids), 1)
        bid = orders.bids[0]
        self.assertEqual((bid.good, bid.tile), ("salt", "a"))
        self.assertGreater(bid.flexible_quantity, 0.0)

    def test_trade_runs_from_cheap_to_dear_only(self):
        orders = plan(merchant(), 4.0, 2.0)
        self.assertEqual([bid.tile for bid in orders.bids], ["b"])

    def test_interest_widens_the_needed_gap(self):
        self.assertEqual(len(plan(merchant(), 2.0, 3.5, rate=0.0).bids), 1)
        self.assertEqual(plan(merchant(), 2.0, 3.5, rate=0.5).bids, ())

    def test_perishable_goods_need_a_wider_gap(self):
        self.assertEqual(len(plan(merchant(), 2.0, 3.5, good="salt").bids), 1)
        self.assertEqual(plan(merchant(), 2.0, 3.5, good="fish").bids, ())
        self.assertEqual(len(plan(merchant(), 2.0, 8.0, good="fish").bids), 1)

    def test_a_merchant_pays_no_more_than_the_trade_breaks_even_at(self):
        # at its ceiling the gap just covers carriage, interest, spoilage and margin
        bid = plan(merchant(), 2.0, 4.0, rate=0.05).bids[0]
        spec = SPECS["salt"]
        price_there = 4.0
        net = price_there - bid.maximum_price - merchants.gap_cost_per_unit(
            spec, bid.maximum_price, price_there, CARRIAGE_PER_UNIT, 0.05)
        self.assertAlmostEqual(net, 0.0, places=9)
        self.assertGreater(bid.maximum_price, 2.0)

    def test_a_merchant_with_no_price_information_does_not_trade(self):
        carriage, area_map, _a, _b = world()
        self.assertEqual(merchants.orders(merchant(), View({}), carriage, area_map, 100.0, {}, SPECS, 0.0).bids, ())


class LimitTests(unittest.TestCase):
    def test_capital_binds(self):
        small = plan(merchant(), 2.0, 5.0, cash=6.0).bids[0]
        big = plan(merchant(), 2.0, 5.0, cash=600.0).bids[0]
        self.assertAlmostEqual(small.flexible_quantity, 6.0 / (2.0 + CARRIAGE_PER_UNIT))
        self.assertLess(small.flexible_quantity, big.flexible_quantity)

    def test_no_cash_no_bid(self):
        self.assertEqual(plan(merchant(), 2.0, 5.0, cash=0.0).bids, ())

    def test_market_share_binds(self):
        bid = plan(merchant(), 2.0, 5.0, cash=1e6).bids[0]
        self.assertAlmostEqual(bid.flexible_quantity, merchants.MERCHANT_MARKET_SHARE * 100.0)

    def test_stock_already_held_at_the_destination_uses_up_the_room(self):
        _c, _m, _a, area_b = world()
        held = {("salt", "b"): merchants.MERCHANT_MARKET_SHARE * 100.0}
        self.assertEqual(plan(merchant(), 2.0, 5.0, cash=1e6, held=held).bids, ())

    def test_held_stock_is_offered_at_the_holding_reservation(self):
        orders = plan(merchant(), 2.0, 2.0, held={("fish", "b"): 7.0}, good="fish", rate=0.25)
        offer = orders.offers[0]
        self.assertEqual((offer.good, offer.tile, offer.quantity), ("fish", "b", 7.0))
        self.assertAlmostEqual(offer.reservation_price, 2.0 * 0.5 / 1.25)


class DispatchAndCloseTests(unittest.TestCase):
    def test_bought_goods_are_carried_and_carriage_is_paid(self):
        carriage, area_map, area_a, _b = world()
        who = merchant()
        orders = plan(who, 2.0, 5.0)
        fills = (Fill("m1", "salt", area_a["salt"], "a", 10.0, 2.0, "buy"),)
        result = merchants.dispatch(who, fills, carriage, SPECS, "coin", 100.0, {("salt", "a"): 10.0})
        self.assertEqual((result.moves[0].tile, result.moves[0].receiver_tile, result.moves[0].quantity), ("a", "b", 10.0))
        self.assertAlmostEqual(result.transfers[0].amount, 10.0 * CARRIAGE_PER_UNIT)
        self.assertEqual(result.transfers[0].payee, merchants.EDGE_CARRIAGE)

    def test_carriage_is_paid_to_whoever_carries_from_the_source_tile(self):
        carriage, _m, area_a, _b = world()
        who = merchant()
        plan(who, 2.0, 5.0)
        fills = (Fill("m1", "salt", area_a["salt"], "a", 10.0, 2.0, "buy"),)
        result = merchants.dispatch(who, fills, carriage, SPECS, "coin", 100.0, {("salt", "a"): 10.0},
                                    carrier_of={"a": "carters of a"}.get)
        self.assertEqual(result.transfers[0].payee, "carters of a")

    def test_stock_worth_more_elsewhere_is_carried_there_not_sold_here(self):
        # stock sitting where it fetches less than elsewhere after carriage is moved, not dumped locally
        who = merchant()
        orders = plan(who, 2.0, 5.0, cash=0.0, held={("salt", "a"): 10.0})
        self.assertEqual([offer.tile for offer in orders.offers], [])
        carriage, _m, _a, _b = world()
        result = merchants.dispatch(who, (), carriage, SPECS, "coin", 100.0, {("salt", "a"): 10.0})
        self.assertEqual((result.moves[0].tile, result.moves[0].receiver_tile, result.moves[0].quantity), ("a", "b", 10.0))

    def test_stock_best_sold_where_it_is_is_offered_there(self):
        orders = plan(merchant(), 5.0, 2.0, cash=0.0, held={("salt", "a"): 10.0})
        self.assertEqual([offer.tile for offer in orders.offers], ["a"])

    def test_goods_it_cannot_pay_to_carry_are_stranded(self):
        carriage, _m, area_a, _b = world()
        who = merchant()
        plan(who, 2.0, 5.0)
        fills = (Fill("m1", "salt", area_a["salt"], "a", 10.0, 2.0, "buy"),)
        result = merchants.dispatch(who, fills, carriage, SPECS, "coin", 4.0, {("salt", "a"): 10.0})
        self.assertAlmostEqual(result.moves[0].quantity, 4.0)
        self.assertEqual(result.stranded, (("salt", "a", 6.0),))

    def test_close_year_moves_expectations_and_pays_the_owner_half_the_profit(self):
        who = merchant(prices={("salt", "x"): 2.0})
        transfers = merchants.close_year(who, {("salt", "x"): 4.0}, {("salt", "x"): 50.0}, 140.0, {},
                                         lambda good, tile: "x", "coin", 0.05)
        self.assertAlmostEqual(who.expected_prices[("salt", "x")], 2.0 + merchants.MERCHANT_EXPECTATION_SPEED * 2.0)
        self.assertEqual(who.expected_volumes[("salt", "x")], 50.0)
        self.assertAlmostEqual(transfers[0].amount, 0.5 * 40.0)
        self.assertEqual(transfers[0].payee, "owner")

    def test_no_payout_without_profit(self):
        self.assertEqual(merchants.close_year(merchant(), {}, {}, 90.0, {}, lambda good, tile: "x", "coin", 0.05), ())

    def test_profit_above_the_interest_rate_is_partly_kept_as_capital(self):
        who = merchant()
        transfers = merchants.close_year(who, {}, {}, 140.0, {}, lambda good, tile: "x", "coin", 0.05)
        self.assertAlmostEqual(transfers[0].amount, merchants.MERCHANT_PROFIT_PAYOUT_SHARE * 40.0)
        self.assertAlmostEqual(who.capital_base, 140.0 - transfers[0].amount)

    def test_profit_below_the_interest_rate_is_all_paid_out(self):
        # trading earns less than lending would: the owner takes the money out rather than stake more
        who = merchant()
        transfers = merchants.close_year(who, {}, {}, 103.0, {}, lambda good, tile: "x", "coin", 0.05)
        self.assertAlmostEqual(transfers[0].amount, 3.0)
        self.assertAlmostEqual(who.capital_base, 100.0)

    def test_a_loss_shrinks_the_capital(self):
        who = merchant()
        merchants.close_year(who, {}, {}, 90.0, {}, lambda good, tile: "x", "coin", 0.05)
        self.assertAlmostEqual(who.capital_base, 90.0)


def mint(agent, amount):
    return Transfer(EDGE_MINT, agent, "coin", amount, "test")


def produce(agent, tile, quantity):
    return GoodsMove(EDGE_PRODUCTION, agent, "salt", tile, quantity, "test")


def run_loop(count, years, capital=500.0):
    """Salt is made in a (120 a year at a reservation of 1) and wanted in b (no local supply); merchants
    carry it from a to b and sell it the following year."""
    carriage, area_map, area_a, area_b = world()
    area_a, area_b = area_a["salt"], area_b["salt"]
    book = Book()
    crowd = [merchant("m%d" % index, prices={("salt", area_a): 2.0, ("salt", area_b): 5.0}) for index in range(count)]
    for who in crowd:
        book.transfer(mint(who.agent_id, capital))
    book.transfer(mint("households", 1e9))
    last = {("salt", area_a): 2.0, ("salt", area_b): 5.0}
    history = []
    for _year in range(years):
        view = View(last)
        book.move(produce("producer", "a", 120.0 - book.stock("producer", "salt", "a")))
        book.move(produce("farmer", "b", 60.0 - book.stock("farmer", "salt", "b")))
        all_orders = []
        for who in crowd:
            held = {(good, tile): book.stock(who.agent_id, good, tile) for good in SPECS for tile in TILES}
            all_orders.append(merchants.orders(who, view, carriage, area_map, book.balance(who.agent_id, "coin"),
                                               held, SPECS, INTEREST_RATE))
        prices, volumes, fills = {}, {}, []
        markets = ((area_a, Bid("households", "salt", area_a, "a", 0.0, 40.0, 2.0, 1.0, 1e9), Offer("producer", "salt", area_a, "a", 120.0, 1.0)),
                   (area_b, Bid("households", "salt", area_b, "b", 0.0, 80.0, 4.0, 1.0, 1e9),
                    Offer("farmer", "salt", area_b, "b", 60.0, 1.5)))
        for area, household_bid, producer_offer in markets:
            bids = [household_bid] + [bid for orders in all_orders for bid in orders.bids if bid.area == area]
            offers = [producer_offer] if producer_offer else []
            offers += [offer for orders in all_orders for offer in orders.offers if offer.area == area]
            result = goods_market.clear(bids, offers, "salt", area, "coin", last.get(("salt", area)))
            settlement.settle_goods(book, result)
            prices[("salt", area)] = result.price
            volumes[("salt", area)] = result.quantity
            fills += result.fills
        shipped = 0.0
        for who in crowd:
            held = {("salt", "a"): book.stock(who.agent_id, "salt", "a")}
            outcome = merchants.dispatch(who, fills, carriage, SPECS, "coin", book.balance(who.agent_id, "coin"), held)
            book.post(outcome.transfers, outcome.moves)
            shipped += sum(move.quantity for move in outcome.moves)
        last = prices
        history.append((prices[("salt", area_a)], prices[("salt", area_b)], shipped))
        for who in crowd:
            held = {("salt", "b"): book.stock(who.agent_id, "salt", "b")}
            merchants.close_year(who, prices, volumes, book.balance(who.agent_id, "coin"), held,
                                 lambda good, tile: area_b, "coin", 0.0)
    return history


class LoopTests(unittest.TestCase):
    def test_trade_narrows_the_gap_toward_carriage(self):
        history = run_loop(count=3, years=14)
        gaps = [high - low for low, high, _shipped in history]
        self.assertGreater(gaps[1], gaps[-1])
        self.assertGreater(gaps[-1], CARRIAGE_PER_UNIT)          # still above carriage: not yet arbitraged away
        self.assertGreater(sum(row[2] for row in history), 0.0)

    def test_many_merchants_overshoot_then_stop_shipping(self):
        history = run_loop(count=6, years=14)
        shipped = [row[2] for row in history]
        self.assertGreater(shipped[0], 0.0)
        self.assertEqual(min(shipped[1:6]), 0.0)                 # the first year's glut stops the next shipments
        self.assertGreater(max(shipped[6:]), 0.0)                # and trade resumes once the stock clears: a cycle
        gaps = [high - low for low, high, _shipped in history]
        self.assertLess(gaps[0], gaps[1])                        # the glut's price effect shows a year on

    def test_more_merchants_ship_more_in_the_first_year(self):
        self.assertGreater(run_loop(count=6, years=1)[0][2], run_loop(count=1, years=1)[0][2])

    def test_the_loop_is_deterministic(self):
        self.assertEqual(run_loop(count=4, years=8), run_loop(count=4, years=8))


if __name__ == "__main__":
    unittest.main()
