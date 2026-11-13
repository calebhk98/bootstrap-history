"""`mint_bid_split.split_bid` divides the mint's bid for its metal over the metal's market areas by where the metal
was traded last year, and `mint_price.paid_in_metal` / `paid_price` say which money regimes pay the metal's sellers up to the
regime's own price. Plain inputs, no game."""

QUICK_TOPIC = True

import unittest

from sim.economy import currency
from sim.economy.mint_bid_split import split_bid
from sim.economy.mint_price import paid_in_metal, paid_price


class SplitBidTests(unittest.TestCase):
    def test_the_bid_follows_the_metal_traded_in_each_area(self):
        shares = split_bid(100.0, {"north": 30.0, "south": 10.0}, {"north": 0.5, "south": 0.5})
        self.assertEqual(shares, {"north": 75.0, "south": 25.0})

    def test_an_area_with_no_metal_on_record_gets_no_bid_while_another_has_some(self):
        shares = split_bid(100.0, {"north": 40.0, "cutoff": 0.0}, {"north": 0.8, "cutoff": 0.2})
        self.assertEqual(shares, {"north": 100.0, "cutoff": 0.0})

    def test_with_no_record_anywhere_the_bid_follows_the_tile_share(self):
        shares = split_bid(100.0, {"north": 0.0, "south": 0.0}, {"north": 0.8, "south": 0.2})
        self.assertEqual(shares, {"north": 80.0, "south": 20.0})

    def test_the_shares_always_add_up_to_the_bid(self):
        shares = split_bid(7.0, {"a": 1.0, "b": 2.0, "c": 4.0}, {"a": 0.2, "b": 0.3, "c": 0.5})
        self.assertAlmostEqual(sum(shares.values()), 7.0)


def spec_of(regime):
    return currency.currency_from_coin_standard("realm", {"regime": regime, "material": "silver_kg", "kg_per_unit": 0.01},
                                                "coin", issuer="state")


class PaidInMetalTests(unittest.TestCase):
    def test_struck_coin_and_weighed_metal_pay_the_metals_sellers_a_stated_price(self):
        self.assertTrue(paid_in_metal(spec_of("struck_coin")))
        self.assertTrue(paid_in_metal(spec_of("weighed_metal")))

    def test_fiat_and_commodity_money_do_not(self):
        self.assertFalse(paid_in_metal(currency.currency_from_coin_standard("x", {"regime": "fiat"}, "note")))
        self.assertFalse(paid_in_metal(spec_of("commodity")))

    def test_weighed_metal_is_paid_its_parity(self):
        spec = spec_of("weighed_metal")
        self.assertEqual(paid_price(spec), currency.mint_parity(spec))


if __name__ == "__main__":
    unittest.main()
