"""The mint's orders and books (sim/economy/mint.py): it holds a real stock of metal, sells only that,
strikes only what it buys, charges a struck coin's issuer-side seigniorage, and exchanges weighed metal
and commodity money at parity with no issuer."""
import types as pytypes
import unittest

from sim.economy import currency, mint
from sim.economy.accounts import Book
from sim.economy.types import EDGE_ISSUE, EDGE_MINT, EDGE_PRODUCTION, GoodsMove, Transfer

METAL = "silver_kg"
PER_UNIT = 0.01


def spec_of(regime, charge=0.0):
    data = {"regime": regime, "material": METAL, "kg_per_unit": PER_UNIT}
    if charge:
        data["mint_charge_share"] = charge
    return currency.currency_from_coin_standard("realm", data, "coin", issuer="state")


class FakeAreaMap:
    """One market area over two tiles."""
    AREA = pytypes.SimpleNamespace(area_id="area", anchor_tile="t1", tiles=("t1", "t2"))

    def goods(self):
        return (METAL,)

    def area_of(self, good, tile):
        return "area"

    def areas(self, good):
        return (self.AREA,)


def economy_of(spec, coin_by_tile=None):
    """A book with coin held by two agents and the opening metal in the mint, as opening.py leaves it."""
    book = Book()
    book.transfer(Transfer(EDGE_ISSUE, "a", "coin", 600.0, "opening"))
    book.transfer(Transfer(EDGE_ISSUE, "b", "coin", 400.0, "opening"))
    setup = pytypes.SimpleNamespace(opening_population_by_tile={"t1": 3.0, "t2": 1.0}, tiles={"t1": 0, "t2": 0})
    record = pytypes.SimpleNamespace(book=book, currency=spec)
    mint.seed_opening_metal(setup, record)
    return setup, record


class OpeningStockTests(unittest.TestCase):
    def test_the_mint_opens_holding_the_metal_in_the_opening_money_by_where_people_live(self):
        _setup, record = economy_of(spec_of("struck_coin"))
        self.assertAlmostEqual(record.book.stock(EDGE_MINT, METAL, "t1"), 1000.0 * PER_UNIT * 0.75)
        self.assertAlmostEqual(record.book.stock(EDGE_MINT, METAL, "t2"), 1000.0 * PER_UNIT * 0.25)

    def test_fiat_has_no_metal_to_hold(self):
        fiat = currency.currency_from_coin_standard("x", {"regime": "fiat"}, "note", issuer="state")
        _setup, record = economy_of(fiat)
        self.assertEqual(record.book.holdings(EDGE_MINT)["goods"], {})


class OrderTests(unittest.TestCase):
    def orders(self, spec, record=None, setup=None):
        if record is None:
            setup, record = economy_of(spec)
        order_book = {}
        held = mint.mint_orders(setup, record, FakeAreaMap(), order_book)
        bids, offers = order_book.get((METAL, "area"), ([], []))
        return held, bids, offers

    def test_it_offers_only_what_it_holds_at_parity(self):
        spec = spec_of("struck_coin")
        _held, _bids, offers = self.orders(spec)
        self.assertAlmostEqual(sum(offer.quantity for offer in offers), 10.0)
        self.assertTrue(all(offer.reservation_price == currency.mint_parity(spec) for offer in offers))

    def test_an_empty_mint_sells_nothing(self):
        spec = spec_of("struck_coin")
        setup, record = economy_of(spec)
        record.book.move_many([GoodsMove(EDGE_MINT, EDGE_PRODUCTION, METAL, tile, record.book.stock(EDGE_MINT, METAL, tile), "emptied")
                               for tile in ("t1", "t2")])
        _held, _bids, offers = self.orders(spec, record, setup)
        self.assertEqual(offers, [])

    def test_a_struck_coins_mint_buys_below_parity_by_its_charge(self):
        spec = spec_of("struck_coin", charge=0.02)
        _held, bids, offers = self.orders(spec)
        self.assertAlmostEqual(bids[0].maximum_price, 0.98 * offers[0].reservation_price)

    def test_weighed_metal_and_commodity_money_are_exchanged_at_parity_both_ways(self):
        for regime in ("weighed_metal", "commodity"):
            spec = spec_of(regime)
            _held, bids, offers = self.orders(spec)
            self.assertEqual(bids[0].maximum_price, offers[0].reservation_price, regime)

    def test_fiat_posts_no_orders(self):
        fiat = currency.currency_from_coin_standard("x", {"regime": "fiat"}, "note", issuer="state")
        setup, record = economy_of(fiat)
        order_book = {}
        self.assertEqual(mint.mint_orders(setup, record, FakeAreaMap(), order_book), {})
        self.assertEqual(order_book, {})


class BooksTests(unittest.TestCase):
    def test_worn_coin_takes_its_metal_with_it(self):
        spec = spec_of("struck_coin")
        setup, record = economy_of(spec)
        record.book.transfer(Transfer("a", "edge:wear", "coin", 100.0, "coin wear"))
        mint.mint_orders(setup, record, FakeAreaMap(), {})
        held = sum(mint.stock_by_tile(record.book, METAL).values())
        self.assertAlmostEqual(held, record.book.money_supply("coin") * PER_UNIT)
        self.assertTrue(record.book.check_conservation(1e-9).ok)

    def strike(self, spec, kilograms):
        """The mint buys metal from a seller at the mint price, as the goods market would settle it."""
        setup, record = economy_of(spec)
        order_book = {}
        before = mint.mint_orders(setup, record, FakeAreaMap(), order_book)
        record.book.move(GoodsMove(EDGE_PRODUCTION, "seller", METAL, "t1", kilograms, "mined"))
        record.book.post([Transfer(EDGE_MINT, "seller", "coin", kilograms * currency.mint_price(spec), "sale")],
                         [GoodsMove("seller", EDGE_MINT, METAL, "t1", kilograms, "sale")])
        mint.settle_mint(record, before)
        return record

    def test_struck_metal_makes_coin_and_the_charge_goes_to_the_issuer(self):
        spec = spec_of("struck_coin", charge=0.02)
        record = self.strike(spec, 5.0)
        self.assertAlmostEqual(record.book.balance("seller", "coin"), 5.0 * 0.98 / PER_UNIT)
        self.assertAlmostEqual(record.book.balance("state", "coin"), 5.0 * 0.02 / PER_UNIT)
        self.assertAlmostEqual(record.book.money_supply("coin") * PER_UNIT, 10.0 + 5.0)
        self.assertAlmostEqual(sum(mint.stock_by_tile(record.book, METAL).values()), 15.0)
        self.assertTrue(record.book.check_conservation(1e-9).ok)

    def test_weighed_metal_has_no_issuer_to_keep_a_charge(self):
        record = self.strike(spec_of("weighed_metal"), 5.0)
        self.assertEqual(record.book.balance("state", "coin"), 0.0)
        self.assertAlmostEqual(record.book.money_supply("coin") * PER_UNIT, 15.0)


if __name__ == "__main__":
    unittest.main()
