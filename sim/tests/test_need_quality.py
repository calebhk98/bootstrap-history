"""A good can serve a need with a quality factor the buyer values; richer buyers weigh it more."""
import json
import os
import unittest

from sim.engine.economy_port_setup import build_setup
from sim.tests.harness import unopened_sim
from sim.world import need_basket

QUALITY_BASIS = {"factor": 0.5, "basis": "test", "conf": "D"}
NEED_DATA = {
    "needs": {"light": {"surplus_budget_share": 1.0, "unit": "lumen-hours"}},
    "goods": {
        "wax": {"satisfies": {"light": 1.0}},
        "tallow": {"satisfies": {"light": 1.0}, "quality": {"light": QUALITY_BASIS}},
    },
}
PRICES = {"wax": 2.0, "tallow": 2.0}


def shares(need_data, reach):
    basket = need_basket.make_basket(need_data, {})
    (need,) = need_basket.with_quality_reach(need_basket.need_prices(basket, PRICES.get), basket, reach)
    return {good: share for good, _price, _effect, share in need.goods}, need


def without_quality(need_data):
    goods = {good: {key: value for key, value in spec.items() if key != "quality"}
             for good, spec in need_data["goods"].items()}
    return {"needs": need_data["needs"], "goods": goods}


class NeedQualityTest(unittest.TestCase):
    def test_a_richer_cohort_shifts_light_spending_to_the_cleaner_good_at_equal_price(self):
        poor, _ = shares(NEED_DATA, need_basket.quality_reach(spending=100.0, floor_cost=95.0))
        rich, _ = shares(NEED_DATA, need_basket.quality_reach(spending=100.0, floor_cost=20.0))
        self.assertGreater(rich["wax"], poor["wax"])
        self.assertLess(rich["tallow"], poor["tallow"])
        self.assertAlmostEqual(sum(rich.values()), 1.0)

    def test_a_cohort_with_nothing_above_its_floors_buys_on_cost_alone(self):
        poor, _ = shares(NEED_DATA, need_basket.quality_reach(spending=100.0, floor_cost=100.0))
        self.assertAlmostEqual(poor["wax"], poor["tallow"])

    def test_quality_changes_the_mix_not_the_need_units_a_good_gives(self):
        _, need = shares(NEED_DATA, 1.0)
        self.assertEqual({good: effect for good, _price, effect, _share in need.goods}, {"wax": 1.0, "tallow": 1.0})

    def test_a_good_with_no_quality_behaves_exactly_as_before_at_any_reach(self):
        plain = without_quality(NEED_DATA)
        basket = need_basket.make_basket(plain, {})
        before = need_basket.need_prices(basket, PRICES.get)
        self.assertEqual(need_basket.with_quality_reach(before, basket, 1.0), before)
        self.assertEqual(before[0].spec.qualities, ())

    def test_quality_declared_in_data_is_read_for_the_light_goods_and_carries_a_basis(self):
        path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "world", "needs.json")
        with open(path, encoding="utf-8") as handle:
            declared = {good: spec["quality"] for good, spec in json.load(handle)["goods"].items() if "quality" in spec}
        self.assertTrue(declared)
        for good, per_need in declared.items():
            for need_id, record in per_need.items():
                self.assertTrue(0.0 < record["factor"] <= 1.0, good)
                self.assertTrue(record["basis"] and record["conf"], good)
                if record.get("heuristic"):
                    self.assertTrue(record["retire"], good)


class RealLightGoodsTest(unittest.TestCase):
    def test_the_real_basket_moves_light_spending_from_tallow_to_cleaner_light_as_reach_rises(self):
        setup = build_setup(unopened_sim(civ="england_1300"))
        basket = setup.basket_for(setup.capital_tile)
        base = need_basket.need_prices(basket, setup.opening_prices.get)
        light_spec = [need.spec for need in base if need.spec.need_id == "light"][0]
        tallow = {good for good, _factor in light_spec.qualities if "tallow" in good}
        self.assertTrue(tallow)

        def tallow_share(reach):
            (light,) = [need for need in need_basket.with_quality_reach(base, basket, reach)
                        if need.spec.need_id == "light"]
            return sum(share for good, _price, _effect, share in light.goods if good in tallow)

        self.assertLess(tallow_share(1.0), tallow_share(0.0))


if __name__ == "__main__":
    unittest.main()
