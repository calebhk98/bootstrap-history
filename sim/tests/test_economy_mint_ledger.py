"""Mint books that follow what was paid and what crossed the border (sim/economy/mint.py): seigniorage is the
coin value of the metal taken in less the coin actually paid for it, and coin that leaves or enters through
edge:external takes its metal with it or arrives with it."""
import unittest

from sim.economy import currency, mint
from sim.economy.types import EDGE_EXTERNAL, EDGE_MINT, EDGE_PRODUCTION, EDGE_WEAR, GoodsMove, Transfer
from sim.tests.test_economy_mint import FakeAreaMap, METAL, PER_UNIT, economy_of, spec_of


def settle_sale(spec, kilograms, price_share_of_strike=1.0, sold_back=0.0):
    """The mint buys `kilograms` at a share of its strike price; optionally melts `sold_back` kg to a buyer at parity."""
    setup, record = economy_of(spec)
    before = mint.mint_orders(setup, record, FakeAreaMap(), {})
    record.book.move(GoodsMove(EDGE_PRODUCTION, "seller", METAL, "t1", kilograms, "mined"))
    paid = kilograms * currency.mint_price(spec) * price_share_of_strike
    record.book.post([Transfer(EDGE_MINT, "seller", "coin", paid, "sale")],
                     [GoodsMove("seller", EDGE_MINT, METAL, "t1", kilograms, "sale")])
    if sold_back:
        record.book.post([Transfer("a", EDGE_MINT, "coin", sold_back * currency.mint_parity(spec), "sale")],
                         [GoodsMove(EDGE_MINT, "a", METAL, "t1", sold_back, "sale")])
    mint.settle_mint(record, before)
    return record


class SeignioragePaidTests(unittest.TestCase):
    def test_a_sale_below_the_strike_price_leaves_the_issuer_the_whole_gap_to_parity(self):
        spec = spec_of("struck_coin", charge=0.02)
        record = settle_sale(spec, 5.0, price_share_of_strike=0.9)
        parity_value = 5.0 * currency.mint_parity(spec)
        self.assertAlmostEqual(record.book.balance("state", "coin"), parity_value - record.book.balance("seller", "coin"))
        self.assertGreater(record.book.balance("state", "coin"), 5.0 * 0.02 / PER_UNIT)

    def test_metal_the_mint_sold_in_the_same_year_does_not_cut_the_charge_on_what_it_bought(self):
        spec = spec_of("struck_coin", charge=0.02)
        record = settle_sale(spec, 5.0, sold_back=2.0)
        self.assertAlmostEqual(record.book.balance("state", "coin"), 5.0 * 0.02 / PER_UNIT)

    def test_money_still_matches_the_metal_held_after_a_cheap_purchase(self):
        spec = spec_of("struck_coin", charge=0.02)
        record = settle_sale(spec, 5.0, price_share_of_strike=0.9)
        held = sum(mint.stock_by_tile(record.book, METAL).values())
        self.assertAlmostEqual(record.book.money_supply("coin") * PER_UNIT, held)


class ForeignCoinTests(unittest.TestCase):
    def test_coin_sent_abroad_takes_its_metal_to_the_external_edge_not_to_wear(self):
        spec = spec_of("struck_coin")
        setup, record = economy_of(spec)
        record.book.transfer(Transfer("a", EDGE_EXTERNAL, "coin", 100.0, "export of coin"))
        mint.mint_orders(setup, record, FakeAreaMap(), {})
        self.assertAlmostEqual(record.book.edge_goods_net(EDGE_EXTERNAL, METAL), -100.0 * PER_UNIT)
        self.assertAlmostEqual(record.book.edge_goods_net(EDGE_WEAR, METAL), 0.0)
        self.assertAlmostEqual(sum(mint.stock_by_tile(record.book, METAL).values()),
                               record.book.money_supply("coin") * PER_UNIT)

    def test_wear_beyond_the_coin_sent_abroad_still_goes_to_wear(self):
        spec = spec_of("struck_coin")
        setup, record = economy_of(spec)
        record.book.transfer(Transfer("a", EDGE_EXTERNAL, "coin", 100.0, "export of coin"))
        record.book.transfer(Transfer("b", EDGE_WEAR, "coin", 50.0, "coin wear"))
        mint.mint_orders(setup, record, FakeAreaMap(), {})
        self.assertAlmostEqual(record.book.edge_goods_net(EDGE_EXTERNAL, METAL), -100.0 * PER_UNIT)
        self.assertAlmostEqual(record.book.edge_goods_net(EDGE_WEAR, METAL), -50.0 * PER_UNIT)

    def test_coin_arriving_from_abroad_arrives_with_its_metal(self):
        spec = spec_of("struck_coin")
        setup, record = economy_of(spec)
        record.book.transfer(Transfer(EDGE_EXTERNAL, "a", "coin", 200.0, "import of coin"))
        mint.mint_orders(setup, record, FakeAreaMap(), {})
        self.assertAlmostEqual(sum(mint.stock_by_tile(record.book, METAL).values()),
                               record.book.money_supply("coin") * PER_UNIT)
        self.assertAlmostEqual(record.book.edge_goods_net(EDGE_EXTERNAL, METAL), 200.0 * PER_UNIT)

    def test_settling_the_mint_books_coin_that_crossed_the_border_during_the_markets(self):
        spec = spec_of("struck_coin", charge=0.02)
        setup, record = economy_of(spec)
        before = mint.mint_orders(setup, record, FakeAreaMap(), {})
        record.book.transfer(Transfer("a", EDGE_EXTERNAL, "coin", 100.0, "export of coin"))
        mint.settle_mint(record, before)
        self.assertAlmostEqual(record.book.edge_goods_net(EDGE_EXTERNAL, METAL), -100.0 * PER_UNIT)
        self.assertEqual(record.book.balance("state", "coin"), 0.0)


if __name__ == "__main__":
    unittest.main()
