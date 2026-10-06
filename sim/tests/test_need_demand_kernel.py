"""The aggregate demand model reads the need-basket kernel: one price index, the economy's surplus split."""
import unittest

from sim.world import demand, need_basket, need_demand

NEED_DATA = {
    "needs": {
        "food": {"surplus_budget_share": 0.4, "subsistence_per_capita_per_year": 100.0},
        "shelter": {"surplus_budget_share": 0.2, "subsistence_per_capita_per_year": 10.0},
        "adornment": {"surplus_budget_share": 0.4},
    },
    "goods": {
        "grain": {"satisfies": {"food": 1.0}},
        "twin_grain": {"satisfies": {"food": 1.0}},
        "timber": {"satisfies": {"shelter": 2.0}},
        "beads": {"satisfies": {"adornment": 1.0}},
    },
}
PRICES = {"grain": 2.0, "twin_grain": 2.0, "timber": 3.0, "beads": 5.0}


def one_bin(income, people=100.0):
    return [demand.IncomeBin(people, income, (0.0, 1.0))]


def need_units_of(quantities, need_data=NEED_DATA):
    basket = need_basket.make_basket(need_data, {})
    return {need.need_id: sum(quantities.get(good, 0.0) * effect for good, effect in need.goods)
            for need in basket.needs}


class AggregateReadsKernelTest(unittest.TestCase):
    def test_an_identical_good_leaves_the_needs_demand_unchanged(self):
        single = {"needs": NEED_DATA["needs"],
                  "goods": {good: spec for good, spec in NEED_DATA["goods"].items() if good != "twin_grain"}}
        bins = one_bin(300.0)
        with_twin = need_demand.NeedDemandModel(NEED_DATA, {}, bins).final_demand(PRICES)
        without = need_demand.NeedDemandModel(single, {}, bins).final_demand(PRICES)
        self.assertAlmostEqual(need_units_of(with_twin)["food"], need_units_of(without, single)["food"])

    def test_above_the_floors_the_aggregate_equals_the_economys_for_one_cohort(self):
        income, people = 300.0, 100.0
        model = need_demand.NeedDemandModel(NEED_DATA, {}, one_bin(income, people))
        aggregate = need_units_of(model.final_demand(PRICES))
        basket = need_basket.make_basket(NEED_DATA, {})
        priced = need_basket.need_prices(basket, PRICES.get)
        floor_cost = need_basket.subsistence_cost_per_person(priced) * people
        _floors, cohort = need_basket.need_units(priced, basket, people, income * people - floor_cost)
        for need_id, units in cohort.items():
            self.assertAlmostEqual(aggregate[need_id], units, places=6)

    def test_demand_rises_with_income_and_the_food_share_falls(self):
        shares, previous = [], None
        for income in (200.0, 400.0, 800.0, 1600.0):
            model = need_demand.NeedDemandModel(NEED_DATA, {}, one_bin(income))
            quantities = model.final_demand(PRICES)
            units = need_units_of(quantities)
            if previous is not None:
                for need_id in units:
                    self.assertGreater(units[need_id], previous[need_id])
            previous = units
            spending = sum(quantity * PRICES[good] for good, quantity in quantities.items())
            shares.append(quantities["grain"] * PRICES["grain"] / spending
                          + quantities["twin_grain"] * PRICES["twin_grain"] / spending)
        self.assertEqual(shares, sorted(shares, reverse=True))

    def test_a_floor_set_by_climate_adds_demand_for_the_goods_that_meet_it(self):
        data = {"needs": dict(NEED_DATA["needs"], shelter={"surplus_budget_share": 0.2,
                                                           "subsistence_from_climate": "shelter_m3"}),
                "goods": NEED_DATA["goods"]}
        model = need_demand.NeedDemandModel(data, {}, one_bin(300.0))
        bare = model.final_demand(PRICES)["timber"]
        model.basket = need_basket.basket_with_floors(model.basket, {"shelter_m3": 20.0})
        self.assertGreater(model.final_demand(PRICES)["timber"], bare)


if __name__ == "__main__":
    unittest.main()
