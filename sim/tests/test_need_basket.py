"""The need-basket kernel: one price index, floors and surplus, read by the economy and the aggregate model."""
import unittest

from sim.economy import households_basket
from sim.world import need_basket

NEED_DATA = {
    "needs": {
        "food": {"surplus_budget_share": 0.5, "subsistence_per_capita_per_year": 200.0},
        "adornment": {"surplus_budget_share": 0.5},
    },
    "goods": {
        "grain": {"satisfies": {"food": 1.0}},
        "twin_grain": {"satisfies": {"food": 1.0}},
        "beads": {"satisfies": {"adornment": 1.0}},
    },
}
PRICES = {"grain": 2.0, "twin_grain": 2.0, "beads": 5.0}


class View:
    year = 1

    def price(self, good, area):
        return PRICES.get(good)

    def area_of(self, good, tile):
        return "area"


def index_by_need(need_data):
    basket = need_basket.make_basket(need_data, {})
    return {need.spec.need_id: need.price_index for need in need_basket.need_prices(basket, PRICES.get)}


class NeedBasketTest(unittest.TestCase):
    def test_economy_priced_needs_equal_the_kernels_for_the_same_prices(self):
        basket = need_basket.make_basket(NEED_DATA, {})
        from_economy = households_basket.need_prices(basket, View(), "tile")
        self.assertEqual(from_economy, need_basket.need_prices(basket, PRICES.get))

    def test_an_identical_good_does_not_change_a_needs_price_index(self):
        single = {"needs": NEED_DATA["needs"],
                  "goods": {good: spec for good, spec in NEED_DATA["goods"].items() if good != "twin_grain"}}
        self.assertAlmostEqual(index_by_need(single)["food"], index_by_need(NEED_DATA)["food"])

    def test_floors_are_paid_first_and_surplus_raises_every_weighted_need(self):
        basket = need_basket.make_basket(NEED_DATA, {})
        priced = need_basket.need_prices(basket, PRICES.get)
        floors, poor = need_basket.need_units(priced, basket, 10.0, 0.0)
        _floors, rich = need_basket.need_units(priced, basket, 10.0, 1000.0)
        self.assertEqual(poor, floors)
        for need_id in rich:
            self.assertGreater(rich[need_id], poor[need_id])

    def test_subsistence_cost_is_floor_units_at_the_price_index(self):
        basket = need_basket.make_basket(NEED_DATA, {})
        priced = need_basket.need_prices(basket, PRICES.get)
        self.assertAlmostEqual(need_basket.subsistence_cost_per_person(priced), 200.0 * index_by_need(NEED_DATA)["food"])


CLIMATE_DATA = {
    "needs": {
        "warmth": {"surplus_budget_share": 0.1, "subsistence_from_climate": "warmth_mj"},
        "food": {"surplus_budget_share": 0.5, "subsistence_per_capita_per_year": 200.0},
    },
    "goods": {"fuel": {"satisfies": {"warmth": 1.0}}, "grain": {"satisfies": {"food": 1.0}}},
}


def floors_of(basket):
    return {need.need_id: need.subsistence_per_person for need in basket.needs}


class ClimateFloorTest(unittest.TestCase):
    def test_a_tiles_floors_equal_the_climate_calculation(self):
        from sim.world import climate_needs
        tile = {"lat": 50, "koppen_class": "Dfb"}
        basket = need_basket.climate_basket(need_basket.make_basket(CLIMATE_DATA, {}), tile)
        self.assertAlmostEqual(floors_of(basket)["warmth"], climate_needs.floors_for_tile(tile)["warmth_mj"])
        self.assertEqual(floors_of(basket)["food"], 200.0)

    def test_a_hotter_tile_has_no_larger_warmth_floor_than_a_colder_one(self):
        base = need_basket.make_basket(CLIMATE_DATA, {})
        cold = floors_of(need_basket.climate_basket(base, {"lat": 62, "koppen_class": "Dfc"}))["warmth"]
        hot = floors_of(need_basket.climate_basket(base, {"lat": 5, "koppen_class": "Af"}))["warmth"]
        self.assertLessEqual(hot, cold)

    def test_a_basket_with_no_climate_need_is_unchanged(self):
        base = need_basket.make_basket(NEED_DATA, {})
        self.assertIs(need_basket.climate_basket(base, {"lat": 50, "koppen_class": "Dfb"}), base)


if __name__ == "__main__":
    unittest.main()
