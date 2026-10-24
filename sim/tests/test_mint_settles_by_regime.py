"""settle_mint (sim/economy/mint.py) after the mint buys freshly mined metal: under every money regime the money stock
rises by the metal's weight, the mint holds the metal of the money in circulation, and the books stay conserved.
Hand-built books, no game."""

QUICK_TOPIC = True

import types as pytypes
import unittest

from sim.economy import currency, mint
from sim.economy.accounts import Book
from sim.economy.types import EDGE_ISSUE, EDGE_MINT, EDGE_PRODUCTION, GoodsMove, Transfer

METAL = "silver_kg"
PER_UNIT = 0.01
OPENING_COIN = 1000.0
MINED_KILOGRAMS = 5.0


def record_after_purchase(regime):
    """Opening money of 1000 units with its metal in the mint, then the mint buys `MINED_KILOGRAMS` at its price."""
    spec = currency.currency_from_coin_standard(
        "realm", {"regime": regime, "material": METAL, "kg_per_unit": PER_UNIT}, "coin", issuer="state")
    book = Book()
    book.transfer(Transfer(EDGE_ISSUE, "a", "coin", OPENING_COIN, "opening"))
    book.move(GoodsMove(EDGE_PRODUCTION, EDGE_MINT, METAL, "t1", OPENING_COIN * PER_UNIT, "metal of the opening money"))
    record = pytypes.SimpleNamespace(book=book, currency=spec)
    held_before = {"t1": OPENING_COIN * PER_UNIT}
    book.move(GoodsMove(EDGE_PRODUCTION, "seller", METAL, "t1", MINED_KILOGRAMS, "mined"))
    book.post([Transfer(EDGE_MINT, "seller", "coin", MINED_KILOGRAMS * currency.mint_price(spec), "sale")],
              [GoodsMove("seller", EDGE_MINT, METAL, "t1", MINED_KILOGRAMS, "sale")])
    mint.settle_mint(record, held_before)
    return record


class SettleMintByRegimeTests(unittest.TestCase):
    def test_metal_the_mint_bought_raises_the_money_stock_under_every_regime(self):
        for regime in ("struck_coin", "weighed_metal", "commodity"):
            record = record_after_purchase(regime)
            self.assertAlmostEqual(record.book.money_supply("coin"), OPENING_COIN + MINED_KILOGRAMS / PER_UNIT, msg=regime)

    def test_the_mint_holds_the_metal_of_the_money_in_circulation_under_every_regime(self):
        for regime in ("struck_coin", "weighed_metal", "commodity"):
            record = record_after_purchase(regime)
            held = sum(mint.stock_by_tile(record.book, METAL).values())
            self.assertAlmostEqual(held, record.book.money_supply("coin") * PER_UNIT, msg=regime)

    def test_the_books_stay_conserved_under_every_regime(self):
        for regime in ("struck_coin", "weighed_metal", "commodity"):
            self.assertTrue(record_after_purchase(regime).book.check_conservation(1e-9).ok, regime)


if __name__ == "__main__":
    unittest.main()
