"""Constants that are really physical quantities are declared in labour hours
(or derived from the deposits) and priced in a coin only when read.
Nothing here builds a game; the mining opex is these hours times the miner's wage."""
QUICK_TOPIC = True

import inspect
import unittest
from types import SimpleNamespace

from sim.constants import REGISTRY
from sim.engine.core import Sim
from sim.resources.labour_profile import mine_labour_hours_per_tonne
from sim.engine.money_units import PricedInLabourHours
from sim.labour.labour_bondage import BondageMixin
from sim.unit_conversions import KILOGRAMS_PER_TONNE
from sim.world import deposits

PHYSICAL_COSTS = {
    "HOUSING_COST_PER_PLACE": "HOUSING_LABOUR_HOURS_PER_PLACE",
    "TRADE_SCHOOL_COST_PER_SEAT": "TRADE_SCHOOL_LABOUR_HOURS_PER_SEAT",
    "INSTITUTION_PLACES_FALLBACK_UPKEEP_PER_HEAD": "INSTITUTION_PLACES_FALLBACK_UPKEEP_LABOUR_HOURS_PER_HEAD",
    "VENTURE_HANDS_PER_REVENUE": "VENTURE_HANDS_PER_REVENUE_LABOUR_HOURS",
    "CREDIT_LINE_PER_FOREST_HA": "CREDIT_LINE_LABOUR_HOURS_PER_FOREST_HA",
    "CAPABILITY_FACTOR_HALF_SATURATION_REV": "CAPABILITY_FACTOR_HALF_SATURATION_REV_LABOUR_HOURS",
    "REVENUE_CEILING_PER_POP_SCALE": "REVENUE_CEILING_LABOUR_HOURS_PER_POP_SCALE",
    "STATE_FUNDING_BASE": "STATE_FUNDING_BASE_LABOUR_HOURS",
}
SLAVE_PRICE = ("SLAVE_BASE_PRICE", "SLAVE_BASE_PRICE_LABOUR_HOURS")
PATRON_GIFT = ("a patron's courting gift", "PATRON_DEATH_COURTING_GIFT_LABOUR_HOURS")   # priced in the coin by the hazards module
FARM_PRICE = ("FARM_LAND_PRICE", "FARM_LABOUR_HOURS_PER_HA")   # priced by the agriculture module's `farm_land_price`
# priced by the resources module (`forest_price`, `nitre_price`, `mine_land_ceiling`) as hours times what an hour is worth
RESOURCES_PRICES = (("FOREST_COST_PER_HA", "FOREST_LABOUR_HOURS_PER_HA"), ("NITRE_COST_PER_M2", "NITRE_LABOUR_HOURS_PER_M2"),
                    ("REVENUE_SCALE_DENARII", "REVENUE_SCALE_LABOUR_HOURS"))


def _deposit(name, grade, depth="surface"):
    return deposits.Deposit(
        name=name, metal="test_metal", tile="nowhere", material_moved="ore", ore_grade_kg_per_tonne=grade,
        depth_class=depth, hardness_class="medium", quantity_tonnes_per_year=100.0, note="")


class PhysicalConstantsAreInHours(unittest.TestCase):

    def test_each_is_declared_in_labour_hours(self):
        for money_name, hours_name in list(PHYSICAL_COSTS.items()) + [SLAVE_PRICE, FARM_PRICE, PATRON_GIFT] + list(RESOURCES_PRICES):
            self.assertTrue(hours_name in REGISTRY, hours_name)
            self.assertIn("labour hour", REGISTRY[hours_name]["unit"], hours_name)

    def test_each_money_name_is_priced_from_its_hours_constant(self):
        for money_name, hours_name in PHYSICAL_COSTS.items():
            declared = inspect.getattr_static(Sim, money_name, None)
            self.assertIsInstance(declared, PricedInLabourHours, money_name)
            self.assertEqual(declared.hours_name, hours_name, money_name)

    def test_a_priced_cost_is_hours_times_the_coin_per_hour(self):
        class Holder:
            COST = PricedInLabourHours("COST_HOURS")
            COST_HOURS = 12.0

            def __init__(self, coin_per_hour):
                self.labour = SimpleNamespace(money_per_labour_hour=lambda: coin_per_hour)

        self.assertAlmostEqual(Holder(0.5).COST, 6.0)
        self.assertAlmostEqual(Holder(4.0).COST, 48.0)
        self.assertEqual(Holder.COST, 12.0)

    def test_the_base_price_of_a_person_is_hours_times_the_coin_per_hour(self):
        host = SimpleNamespace(SLAVE_BASE_PRICE_LABOUR_HOURS=300.0, money_per_labour_hour=lambda: 0.25)
        self.assertAlmostEqual(BondageMixin.SLAVE_BASE_PRICE.fget(host), 75.0)

    def test_no_curated_mining_opex_remains(self):
        self.assertFalse([name for name in REGISTRY if name.startswith("MINE_OPEX_PER_T_")])

    def test_mining_running_hours_are_the_deposits_extraction_labour_weighted_by_output(self):
        lean, rich = _deposit("lean", 5.0, "deep_vein"), _deposit("rich", 50.0)
        _build, running = mine_labour_hours_per_tonne([(lean, 0.25), (rich, 0.75)], {})
        expected = KILOGRAMS_PER_TONNE * (0.25 * deposits.extraction_cost_labour_hours_per_kg(lean)
                                          + 0.75 * deposits.extraction_cost_labour_hours_per_kg(rich))
        self.assertAlmostEqual(running, expected, delta=1e-9)
        self.assertGreater(running, mine_labour_hours_per_tonne([(rich, 1.0)], {})[1])

    def test_mining_build_hours_are_the_deposits_shaft_labour_weighted_by_output(self):
        lean, rich = _deposit("lean", 5.0, "deep_vein"), _deposit("rich", 50.0)
        build, _running = mine_labour_hours_per_tonne([(lean, 0.5), (rich, 0.5)], {})
        expected = 0.5 * (deposits.build_cost_labour_hours_per_tonne_year(lean)
                          + deposits.build_cost_labour_hours_per_tonne_year(rich))
        self.assertAlmostEqual(build, expected, delta=1e-9)


if __name__ == "__main__":
    unittest.main()
