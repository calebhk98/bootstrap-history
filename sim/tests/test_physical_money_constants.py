"""Constants that are really physical quantities are declared in labour hours
(or derived from the deposits) and priced in a coin only when read."""
import random
import unittest

from sim.constants import REGISTRY, book_money_names
from sim.engine import data
from sim.engine.core import Sim
from sim.world import deposits
from sim.unit_conversions import KILOGRAMS_PER_TONNE

PHYSICAL_COSTS = {
    "FARM_COST_PER_HA": "FARM_LABOUR_HOURS_PER_HA",
    "FOREST_COST_PER_HA": "FOREST_LABOUR_HOURS_PER_HA",
    "HOUSING_COST_PER_PLACE": "HOUSING_LABOUR_HOURS_PER_PLACE",
    "TRADE_SCHOOL_COST_PER_SEAT": "TRADE_SCHOOL_LABOUR_HOURS_PER_SEAT",
    "NITRE_COST_PER_M2": "NITRE_LABOUR_HOURS_PER_M2",
    "LIVING_COST_BASE_SUBSISTENCE": "LIVING_COST_BASE_SUBSISTENCE_LABOUR_HOURS",
    "LIVING_COST_HOUSEHOLD_BASE": "LIVING_COST_HOUSEHOLD_BASE_LABOUR_HOURS",
    "INSTITUTION_PLACES_FALLBACK_UPKEEP_PER_HEAD": "INSTITUTION_PLACES_FALLBACK_UPKEEP_LABOUR_HOURS_PER_HEAD",
    "VENTURE_HANDS_PER_REVENUE": "VENTURE_HANDS_PER_REVENUE_LABOUR_HOURS",
    "SLAVE_BASE_PRICE": "SLAVE_BASE_PRICE_LABOUR_HOURS",
    "CREDIT_LINE_PER_FOREST_HA": "CREDIT_LINE_LABOUR_HOURS_PER_FOREST_HA",
    "CAPABILITY_FACTOR_HALF_SATURATION_REV": "CAPABILITY_FACTOR_HALF_SATURATION_REV_LABOUR_HOURS",
    "REVENUE_CEILING_PER_POP_SCALE": "REVENUE_CEILING_LABOUR_HOURS_PER_POP_SCALE",
    "STATE_FUNDING_BASE": "STATE_FUNDING_BASE_LABOUR_HOURS",
    "REVENUE_SCALE_DENARII": "REVENUE_SCALE_LABOUR_HOURS",
    "PATRON_DEATH_COURTING_GIFT": "PATRON_DEATH_COURTING_GIFT_LABOUR_HOURS",
}


def build(civ_name):
    from sim.tests import harness
    sim = Sim(harness.NODES, harness.ORDER, random.Random(1), events=False,
              manual=True, civ=data.load_civ(civ_name))
    sim.goal, sim.done_year = harness.GOAL, {}
    return sim


class PhysicalConstantsAreInHours(unittest.TestCase):

    def test_each_is_declared_in_labour_hours_not_book_money(self):
        for money_name, hours_name in PHYSICAL_COSTS.items():
            self.assertTrue(hours_name in REGISTRY, hours_name)
            self.assertIn("labour hour", REGISTRY[hours_name]["unit"], hours_name)
            self.assertFalse(REGISTRY[hours_name]["book_money"], hours_name)
            self.assertNotIn(money_name, book_money_names())

    def test_price_is_hours_times_the_coin_per_hour(self):
        for civ_name in ("rome_100ad", "han_china_100ad"):
            sim = build(civ_name)
            for money_name, hours_name in PHYSICAL_COSTS.items():
                self.assertAlmostEqual(
                    getattr(sim.labour if hasattr(sim.labour, money_name) else sim, money_name),
                    REGISTRY[hours_name]["value"] * sim.labour.money_per_labour_hour(),
                    delta=1e-9, msg=(civ_name, money_name))

    def test_no_curated_mining_opex_remains(self):
        self.assertFalse([name for name in REGISTRY if name.startswith("MINE_OPEX_PER_T_")])

    def test_mining_opex_is_the_deposits_extraction_labour_at_the_miner_wage(self):
        sim = build("rome_100ad")
        for metal in ("lead", "silver", "copper"):
            hours = sum(weight * KILOGRAMS_PER_TONNE
                        * deposits.extraction_cost_labour_hours_per_kg(deposit)
                        for deposit, weight in sim._mine_reference_deposits(metal))
            self.assertAlmostEqual(sim._mine_opex(metal), hours * sim.labour.wage_per_hour("miner"),
                                   delta=1e-6, msg=metal)


if __name__ == "__main__":
    unittest.main()
