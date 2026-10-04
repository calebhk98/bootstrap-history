"""Money with no issuer takes into circulation only what holders want to add, plus what is lost: a
money commodity that is cheap to make does not flood the money stock (and the land) at parity."""
import dataclasses
import unittest

from sim.economy import mint
from sim.economy.economy import Economy
from sim.economy.types import CurrencySpec, Recipe
from sim.tests import economy_fixture as fixture


def cheap_money_setup(regime):
    """The fixture's metal made twenty times cheaper than its parity, as the money of `regime`."""
    recipes = fixture.recipes()
    recipes[fixture.SMELT] = dataclasses.replace(recipes[fixture.SMELT], outputs={fixture.METAL: 20.0})
    issuer = "state:fixture" if regime == "struck_coin" else None
    money = CurrencySpec("coin", regime, fixture.METAL, 0.01, issuer, 0.05 if regime == "struck_coin" else 0.0)
    return fixture.small_setup(recipes=recipes, currency=money)


class MonetisationTests(unittest.TestCase):
    def test_a_commodity_money_takes_in_what_holders_want_plus_what_spoils(self):
        setup = cheap_money_setup("commodity")
        economy = Economy(setup)
        record = economy.record
        supply = record.book.money_supply(setup.currency_id)
        wanted = (sum(cohort.cash_target for cohort in record.cohorts.values())
                  + sum(producer.cash_target for producer in record.producers.values())
                  + sum(merchant.capital_base for merchant in record.merchants.values()))
        expected = max(0.0, wanted - supply) + setup.specs[fixture.METAL].spoilage_per_year * supply
        self.assertAlmostEqual(mint.yearly_monetisation(setup, record), expected)

    def test_a_struck_coin_keeps_its_mint_capacity(self):
        setup = cheap_money_setup("struck_coin")
        record = Economy(setup).record
        self.assertAlmostEqual(mint.yearly_monetisation(setup, record),
                               mint.MINT_YEARLY_STRIKE_SHARE * record.book.money_supply(setup.currency_id))

    def test_the_mint_bids_no_more_than_holders_want_when_their_cash_is_full(self):
        setup = cheap_money_setup("commodity")
        economy = Economy(setup)
        record = economy.record
        supply = record.book.money_supply(setup.currency_id)
        for cohort_id, cohort in list(record.cohorts.items()):
            record.cohorts[cohort_id] = dataclasses.replace(cohort, cash_target=0.0)
        order_book = {}
        mint.mint_orders(setup, record, economy.area_map, order_book)
        bid = sum(each.flexible_quantity for bids, _offers in order_book.values() for each in bids
                  if each.buyer == mint.EDGE_MINT)
        loss = setup.specs[fixture.METAL].spoilage_per_year * supply * setup.currency.backing_per_unit
        self.assertLessEqual(bid, loss + 1e-9)
        coin_book = {}
        coin = cheap_money_setup("struck_coin")
        coined = Economy(coin)
        mint.mint_orders(coin, coined.record, coined.area_map, coin_book)
        struck = sum(each.flexible_quantity for bids, _offers in coin_book.values() for each in bids
                     if each.buyer == mint.EDGE_MINT)
        self.assertGreater(struck, bid)


if __name__ == "__main__":
    unittest.main()
