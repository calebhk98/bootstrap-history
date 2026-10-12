"""Final demand while one price moves equals final demand recomputed whole at each price, to the last bit."""

QUICK_TOPIC = True

import unittest

from sim.world import demand, need_basket, need_demand, need_final_demand

NEEDS = {
    "needs": {
        "food": {"surplus_budget_share": 0.4, "subsistence_per_capita_per_year": 200.0},
        "protection": {"surplus_budget_share": 0.4, "subsistence_per_capita_per_year": 2.0},
        "health": {"surplus_budget_share": 0.2},
    },
    "goods": {
        "wheat_kg": {"satisfies": {"food": 1.0}},
        "barley_kg": {"satisfies": {"food": 0.7}},
        "bronze_kg": {"satisfies": {"protection": 1.0, "health": 0.3}},
        "iron_kg": {"satisfies": {"protection": 2.0}},
        "herb_kg": {"satisfies": {"health": 1.0}},
    },
}
PRODUCTION = {
    "wheat_kg": {"outputs": {"wheat_kg": 100.0}, "inputs": {}, "labour_hours": {"labourer": 10.0}},
}
PRICES = {"wheat_kg": 0.3, "barley_kg": 0.4, "bronze_kg": 5.0, "iron_kg": 3.0, "herb_kg": 2.0}
TRIAL_PRICES = (1e-9, 0.01, 0.3, 2.5, 40.0, 1e6)


def whole_evaluation(model, prices, material, price, weights):
    """The straightforward reading: copy the prices, price every need, add up the weighted demand."""
    trial = dict(prices)
    trial[material] = price
    final = model.final_demand(trial)
    return final.get(material, 0.0), sum(weights.get(source, 0.0) * units for source, units in final.items())


class SingleMaterialTrialTest(unittest.TestCase):
    def assert_trial_equals_whole(self, mean_income, material):
        bins = demand.income_bins(1_000_000.0, mean_income)
        model = need_demand.NeedDemandModel(NEEDS, PRODUCTION, bins)
        weights = {"wheat_kg": 1.0, "bronze_kg": 0.5, "herb_kg": 2.0}
        trial = need_final_demand.SingleMaterialTrial(model, PRICES, material, weights)
        for price in TRIAL_PRICES:
            self.assertEqual(trial.weighted_final(price),
                             whole_evaluation(model, PRICES, material, price, weights),
                             "%s at %g, mean income %g" % (material, price, mean_income))
            trial_prices = dict(PRICES, **{material: price})
            self.assertEqual(trial.final_demand(price), model.final_demand(trial_prices))

    def test_every_material_at_incomes_above_and_below_the_floor_line(self):
        for mean_income in (0.5, 100.0, 550.0, 5000.0):
            for material in PRICES:
                self.assert_trial_equals_whole(mean_income, material)

    def test_a_material_no_need_lists_changes_nothing(self):
        bins = demand.income_bins(1_000_000.0, 300.0)
        model = need_demand.NeedDemandModel(NEEDS, PRODUCTION, bins)
        trial = need_final_demand.SingleMaterialTrial(model, PRICES, "unlisted_kg", {})
        self.assertEqual(trial.weighted_final(1.0), trial.weighted_final(50.0))

    def test_spending_split_gives_the_per_good_quantity(self):
        good = demand.Good("food", 200.0, 0.6)
        for income, committed in ((10.0, 100.0), (100.0, 100.0), (400.0, 100.0), (50.0, 0.0), (0.0, 100.0)):
            scale, flexible = demand.household_spending_split(income, committed)
            self.assertEqual(
                demand.household_quantity_demanded_given_committed(good, 3.0, income, committed),
                good.subsistence_quantity_per_capita_per_year * scale
                + (good.marginal_budget_share / 3.0) * flexible)

    def test_priced_need_loop_equals_need_prices(self):
        basket = need_basket.make_basket(NEEDS, PRODUCTION)
        exponent = 1.0 - basket.substitution
        looped = [need_basket.priced_need(spec, exponent, PRICES.get) for spec in basket.needs]
        self.assertEqual([need for need in looped if need is not None],
                         need_basket.need_prices(basket, PRICES.get))


if __name__ == "__main__":
    unittest.main()
