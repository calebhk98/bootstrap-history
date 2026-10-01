"""A durable luxury saturates per head: the budget share is the data's, the metal bought is bounded."""
import unittest

from sim.world import demand, need_demand

POPULATION = 1_000_000.0
MEAN_INCOME = 550.0
SATIATION = 0.002  # need units per head per year in these fixtures

PRODUCTION = {
    "wheat_kg": {"outputs": {"wheat_kg": 100.0}, "inputs": {}, "labour_hours": {"labourer": 10.0}},
    "silver_kg": {"outputs": {"silver_kg": 1.0}, "inputs": {}, "labour_hours": {"labourer": 100.0}},
    "tool_kg": {"outputs": {"tool_kg": 1.0}, "inputs": {}, "labour_hours": {"labourer": 10.0}},
}


def needs(satiation):
    ornament = {"surplus_budget_share": 0.2}
    if satiation is not None:
        ornament["satiation_per_capita_per_year"] = satiation
    return {
        "needs": {"food": {"surplus_budget_share": 0.5, "subsistence_per_capita_per_year": 200.0},
                  "tools": {"surplus_budget_share": 0.3}, "ornament": ornament},
        "goods": {"wheat_kg": {"satisfies": {"food": 1.0}},
                  "tool_kg": {"satisfies": {"tools": 1.0}},
                  "silver_kg": {"satisfies": {"ornament": 1.0}}},
    }


def demand_at(silver_price, satiation):
    model = need_demand.NeedDemandModel(
        needs(satiation), PRODUCTION, demand.income_bins(POPULATION, MEAN_INCOME))
    prices = {"wheat_kg": 0.5, "tool_kg": 5.0, "silver_kg": silver_price}
    return model.final_demand(prices), prices


def spending(quantities, prices):
    return sum(quantities[material] * prices[material] for material in quantities)


class OrnamentSaturationTest(unittest.TestCase):

    def test_ornament_spending_is_its_budget_share_whatever_the_metal_costs(self):
        # Satiation far above what the budget buys: the cap does not bind.
        shares = []
        for silver_price in (1.0, 10.0, 100.0):
            quantities, prices = demand_at(silver_price, 1e9)
            shares.append(quantities["silver_kg"] * silver_price / spending(quantities, prices))
        self.assertAlmostEqual(shares[0], shares[1], places=6)
        self.assertAlmostEqual(shares[1], shares[2], places=6)

    def test_cheap_metal_is_bought_only_up_to_the_satiation_per_head(self):
        quantities, _prices = demand_at(0.01, SATIATION)
        self.assertLessEqual(quantities["silver_kg"], SATIATION * POPULATION * (1 + 1e-9))

    def test_budget_over_the_cap_is_spent_on_other_needs_not_lost(self):
        capped, prices = demand_at(0.01, SATIATION)
        free, _prices = demand_at(0.01, None)
        self.assertAlmostEqual(spending(capped, prices), spending(free, prices),
                               delta=1e-6 * spending(free, prices))
        self.assertGreater(capped["wheat_kg"], free["wheat_kg"])

    def test_shipped_households_buy_a_plausible_mass_of_bright_metal(self):
        # Validation only: a few grams a head a year is the order a durable ornament stock wears and
        # is lost at; thousands of tonnes for a first-century empire is not.
        from sim.engine import foreign_capacity
        from sim.engine.data import load_civ
        for civilization_id in ("rome_100ad", "han_china_100ad"):
            tonnes = foreign_capacity.household_tonnes_by_material(civilization_id)
            grams_per_head = (tonnes.get("silver_kg", 0.0) + tonnes.get("gold_kg", 0.0)) * 1e6 \
                / float(load_civ(civilization_id)["population"])
            self.assertLessEqual(grams_per_head, 2.0, civilization_id)


if __name__ == "__main__":
    unittest.main()
