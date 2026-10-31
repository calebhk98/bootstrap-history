"""Money with no issuer takes into circulation only what holders want to add, plus what is lost: a
money commodity that is cheap to make does not flood the money stock (and the land) at parity."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import mint
from sim.economy.metal_stock import COIN_WEAR_PER_YEAR, METAL_GOODS_LOSS_PER_YEAR
from sim.economy.types import CurrencySpec, GoodSpec

METAL = "metal_kg"
SUPPLY = 1000.0
SPOILAGE = 0.02


class StandInBook:
    """What the mint reads of the book: a money supply and no metal in the mint's hands."""

    def money_supply(self, currency_id):
        return SUPPLY

    def holdings(self, agent):
        return {"goods": {}}

    def edge_net(self, edge, currency_id):
        return 0.0


def setup_and_record(regime, cash_target=40.0):
    """Two cohorts, a producer and a merchant with cash targets, whose money is `regime` made of METAL."""
    issuer = "state:fixture" if regime == "struck_coin" else None
    spec = CurrencySpec("coin", regime, METAL, 0.01, issuer, 0.05 if regime == "struck_coin" else 0.0)
    setup = types.SimpleNamespace(specs={METAL: GoodSpec(METAL, 1.0, SPOILAGE, 0.0, "metal")}, tiles={"town": None}, currency_id="coin")
    record = types.SimpleNamespace(
        currency=spec, book=StandInBook(),
        cohorts={name: types.SimpleNamespace(cash_target=cash_target) for name in ("a", "b")},
        producers={"p": types.SimpleNamespace(cash_target=cash_target)},
        merchants={"m": types.SimpleNamespace(capital_base=cash_target)})
    return setup, record


def bid_capacity(setup, record):
    area = types.SimpleNamespace(area_id="area", anchor_tile="town", tiles=("town",))
    area_map = types.SimpleNamespace(goods=lambda: [METAL], areas=lambda good: [area], area_of=lambda good, tile: "area")
    order_book = {}
    mint.mint_orders(setup, record, area_map, order_book)
    return sum(each.flexible_quantity for bids, _offers in order_book.values() for each in bids if each.buyer == mint.EDGE_MINT)


class MonetisationTests(unittest.TestCase):
    def test_a_commodity_money_takes_in_what_holders_want_plus_what_spoils(self):
        setup, record = setup_and_record("commodity", cash_target=400.0)
        wanted = 4 * 400.0
        self.assertAlmostEqual(mint.yearly_monetisation(setup, record), (wanted - SUPPLY) + SPOILAGE * SUPPLY)

    def test_a_commodity_money_whose_holders_want_no_more_takes_in_only_what_spoils(self):
        setup, record = setup_and_record("commodity", cash_target=10.0)
        self.assertAlmostEqual(mint.yearly_monetisation(setup, record), SPOILAGE * SUPPLY)

    def test_a_struck_coin_takes_in_what_holders_want_plus_what_wears(self):
        setup, record = setup_and_record("struck_coin", cash_target=400.0)
        wanted = 4 * 400.0
        self.assertAlmostEqual(mint.yearly_monetisation(setup, record), (wanted - SUPPLY) + COIN_WEAR_PER_YEAR * SUPPLY)

    def test_a_struck_coin_whose_holders_want_no_more_takes_in_only_what_wears(self):
        setup, record = setup_and_record("struck_coin", cash_target=10.0)
        self.assertAlmostEqual(mint.yearly_monetisation(setup, record), COIN_WEAR_PER_YEAR * SUPPLY)

    def test_weighed_metal_whose_holders_want_no_more_takes_in_only_what_is_lost(self):
        setup, record = setup_and_record("weighed_metal", cash_target=10.0)
        self.assertAlmostEqual(mint.yearly_monetisation(setup, record), METAL_GOODS_LOSS_PER_YEAR * SUPPLY)


class MintOrderTests(unittest.TestCase):
    def test_the_mint_bids_no_more_than_holders_want_when_their_cash_is_full(self):
        setup, record = setup_and_record("commodity", cash_target=0.0)
        self.assertLessEqual(bid_capacity(setup, record), SPOILAGE * SUPPLY * record.currency.backing_per_unit + 1e-9)

    def test_a_struck_coin_mint_bids_no_more_than_holders_want_when_their_cash_is_full(self):
        setup, record = setup_and_record("struck_coin", cash_target=0.0)
        self.assertAlmostEqual(bid_capacity(setup, record), COIN_WEAR_PER_YEAR * SUPPLY * record.currency.backing_per_unit)


if __name__ == "__main__":
    unittest.main()
