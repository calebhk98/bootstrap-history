"""A good that serves a need may declare the largest share of the need's units it can meet (`max_share_of_need`)."""

QUICK_TOPIC = True

import copy
import unittest

from sim.world import need_basket

NEED_DATA = {
    "needs": {"food": {"surplus_budget_share": 0.5, "subsistence_per_capita_per_year": 200.0}},
    "goods": {
        "grain": {"satisfies": {"food": 1.0}},
        "tallow": {"satisfies": {"food": 2.0}},
    },
}
PRICES = {"grain": 1.0, "tallow": 0.2}      # tallow is far cheaper per unit of food


def unit_shares(need_data):
    basket = need_basket.make_basket(need_data, {})
    (need,) = need_basket.need_prices(basket, PRICES.get)
    units = {good: share * effect / price for good, price, effect, share in need.goods}
    total = sum(units.values())
    return {good: value / total for good, value in units.items()}, need


class ShareLimitTests(unittest.TestCase):

    def test_cheap_limited_good_buys_at_most_its_share(self):
        limited = copy.deepcopy(NEED_DATA)
        limited["goods"]["tallow"]["max_share_of_need"] = {"food": 0.35}
        shares, _need = unit_shares(limited)
        self.assertAlmostEqual(shares["tallow"], 0.35)
        self.assertAlmostEqual(shares["grain"], 0.65)

    def test_without_the_field_nothing_changes(self):
        shares, _need = unit_shares(NEED_DATA)
        self.assertGreater(shares["tallow"], 0.9)

    def test_a_limit_above_the_uncapped_share_changes_nothing(self):
        limited = copy.deepcopy(NEED_DATA)
        limited["goods"]["tallow"]["max_share_of_need"] = {"food": 0.999}
        self.assertEqual(unit_shares(limited)[0], unit_shares(NEED_DATA)[0])

    def test_limit_raises_the_price_of_a_unit_and_spending_shares_sum_to_one(self):
        limited = copy.deepcopy(NEED_DATA)
        limited["goods"]["tallow"]["max_share_of_need"] = {"food": 0.35}
        _shares, capped = unit_shares(limited)
        _shares, free = unit_shares(NEED_DATA)
        self.assertGreater(capped.price_index, free.price_index)
        self.assertAlmostEqual(sum(row[3] for row in capped.goods), 1.0)

    def test_the_limit_holds_in_the_units_bought(self):
        limited = copy.deepcopy(NEED_DATA)
        limited["goods"]["tallow"]["max_share_of_need"] = {"food": 0.35}
        basket = need_basket.make_basket(limited, {})
        priced = need_basket.need_prices(basket, PRICES.get)
        _floors, totals = need_basket.need_units(priced, basket, 10.0, 500.0)
        (need,) = priced
        spent_units = {good: share * effect / price for good, price, effect, share in need.goods}
        self.assertAlmostEqual(spent_units["tallow"] / sum(spent_units.values()), 0.35)
        self.assertGreater(totals["food"], 0.0)


if __name__ == "__main__":
    unittest.main()
